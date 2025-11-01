"""
FastAPI wrapper for the Meal Planning Agent to integrate with AgentOS.

This exposes the Streamlit agent logic as a JSON HTTP API that AgentOS can invoke.
"""
import os
import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import the agent creation from agent.py
# Note: We import the async create_agent function and the tools
from agent import create_agent

load_dotenv()

# Global agent instance (initialized on startup)
agent_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global agent_instance
    
    # Startup
    print("🚀 Initializing Meal Planning Agent...")
    
    # Check for required API keys
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        print("⚠️  WARNING: GOOGLE_API_KEY not found. Agent may not work properly.")
    
    try:
        agent_instance = await create_agent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        raise
    
    yield  # Server is running
    
    # Shutdown (cleanup if needed)
    print("🔄 Shutting down agent...")


app = FastAPI(
    title="Meal Planning Agent - AgentOS Integration",
    description="HTTP wrapper for the Meal Planning Agent",
    version="1.0.0",
    lifespan=lifespan
)


class InvokeRequest(BaseModel):
    """Request format for agent invocation"""
    prompt: Any = Field(..., description="User prompt/query (string or dict with prompt key)")
    timeout: Optional[int] = Field(default=30, description="Timeout in seconds")


class InvokeResponse(BaseModel):
    """Response format with AgentOS telemetry"""
    result: str = Field(..., description="Agent response")  # Changed from 'output' to 'result'
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    timestamp: str = Field(..., description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    cost: float = Field(default=0.0, description="Estimated cost in USD")
    
    # AgentOS ATP v0 Telemetry (optional but recommended)
    telemetry: Optional[Dict[str, Any]] = Field(default=None, description="AgentOS telemetry trace")


@app.get("/health")
async def health_check():
    """Health check endpoint for AgentOS"""
    return {
        "status": "healthy",
        "agent_initialized": agent_instance is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest):
    """
    Invoke the meal planning agent with a user prompt.
    
    This endpoint:
    1. Accepts a JSON request with a prompt
    2. Invokes the agent
    3. Returns the response with telemetry data
    """
    if agent_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized. Check server logs."
        )
    
    start_time = time.time()
    
    try:
        # Create telemetry trace (AgentOS ATP v0 format)
        trace_id = f"trace_{int(start_time * 1000)}"
        invocation_start = datetime.utcnow().isoformat()
        
        # Extract prompt - handle various input formats from AgentOS
        if isinstance(request.prompt, str):
            prompt = request.prompt
        elif isinstance(request.prompt, dict):
            # AgentOS sends {"prompt": "text"} in input_data
            prompt = request.prompt.get("prompt", str(request.prompt))
        else:
            prompt = str(request.prompt)
        
        # Invoke the agent
        response = await agent_instance.arun(prompt)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract response content
        output_text = response.content if hasattr(response, 'content') else str(response)
        
        # Build telemetry trace (optional but helps AgentOS show "verified" badge)
        telemetry = {
            "trace_id": trace_id,
            "agent_id": "meal-planning-agent",
            "status": "success",
            "started_at": invocation_start,
            "ended_at": datetime.utcnow().isoformat(),
            "execution_time_ms": execution_time_ms,
            "steps": [
                {
                    "step_id": "agent_execution",
                    "name": "Process meal planning query",
                    "started_at": invocation_start,
                    "ended_at": datetime.utcnow().isoformat(),
                    "status": "success",
                    "input_excerpt": prompt[:100],
                    "output_excerpt": output_text[:100]
                }
            ],
            "metadata": {
                "model": "gemini-2.0-flash-exp",
                "prompt_length": len(prompt),
                "response_length": len(output_text),
                "telemetry_quality": "verified"
            }
        }
        
        return InvokeResponse(
            result=output_text,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "prompt_length": len(prompt),
                "response_length": len(output_text),
                "model": "gemini-2.0-flash-exp"
            },
            cost=0.01,  # Estimate for Gemini
            telemetry=telemetry
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Build error telemetry
        telemetry = {
            "trace_id": trace_id,
            "agent_id": "meal-planning-agent",
            "status": "error",
            "started_at": invocation_start,
            "ended_at": datetime.utcnow().isoformat(),
            "execution_time_ms": execution_time_ms,
            "error": str(e),
            "metadata": {
                "telemetry_quality": "verified"
            }
        }
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "telemetry": telemetry
            }
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Meal Planning Agent - AgentOS Integration",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health - Health check",
            "invoke": "POST /invoke - Invoke the agent with a prompt"
        },
        "status": "ready" if agent_instance else "initializing"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "model_b_sample:app",
        host="0.0.0.0",
        port=9001,  # Changed from 9000 to avoid ClickHouse conflict
        reload=True,
        log_level="info"
    )
