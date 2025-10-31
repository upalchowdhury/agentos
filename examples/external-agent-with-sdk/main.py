"""
Example external agent (Model B) using AgentOS Python SDK.

This demonstrates how to build an external agent that sends
verified telemetry to AgentOS platform.

Requirements:
    pip install agentos-sdk fastapi uvicorn openai
"""

import os
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# AgentOS SDK imports
from agentos_sdk import AgentOSClient, StepKind, InvocationStatus

app = FastAPI(title="Example External Agent with AgentOS SDK")


class InvokeRequest(BaseModel):
    """Request model for agent invocation"""
    query: str
    context: Dict[str, Any] = {}


class InvokeResponse(BaseModel):
    """Response model for agent invocation"""
    result: str
    execution_time_ms: int
    trace_id: str
    invocation_id: str
    telemetry_status: str


@app.post("/invoke")
async def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    """
    Invoke the agent with telemetry tracking via AgentOS SDK.
    
    This endpoint:
    1. Receives invocation request
    2. Creates telemetry context
    3. Executes agent logic with step tracking
    4. Auto-sends ATP v0 telemetry to AgentOS
    5. Returns result with trace ID
    """
    
    # Initialize AgentOS client
    agentos_base_url = os.getenv("AGENTOS_URL", "http://localhost:8000")
    agentos_api_key = os.getenv("AGENTOS_API_KEY", "demo-key")
    
    client = AgentOSClient(
        base_url=agentos_base_url,
        api_key=agentos_api_key
    )
    
    # Agent configuration
    org_id = os.getenv("AGENTOS_ORG_ID", "org-demo")
    project_id = os.getenv("AGENTOS_PROJECT_ID", "proj-demo")
    agent_id = os.getenv("AGENTOS_AGENT_ID", "agent-demo")
    
    start_time = time.time()
    
    try:
        # Start telemetry context (auto-sends on exit)
        with client.trace(
            org_id=org_id,
            project_id=project_id,
            agent_id=agent_id,
            version_id="v1.0",
            auto_send=True
        ) as telemetry:
            
            # Step 1: Parse query
            with telemetry.step("parse_query", StepKind.SYSTEM) as step:
                parsed_query = request.query.strip().lower()
                step.set_input(request.query[:200])
                step.set_output(f"Parsed: {parsed_query[:100]}")
            
            # Step 2: Retrieve context (simulated)
            with telemetry.step("retrieve_context", StepKind.TOOL) as step:
                # Simulate context retrieval
                time.sleep(0.05)
                context_docs = ["doc1", "doc2", "doc3"]
                step.set_input(f"query={parsed_query}")
                step.set_output(f"Retrieved {len(context_docs)} documents")
            
            # Step 3: Generate response (simulated LLM call)
            with telemetry.step("generate_response", StepKind.PROMPT) as step:
                # Simulate LLM API call
                time.sleep(0.1)
                
                # Mock response generation
                response_text = f"Response to: {request.query}"
                
                # Track model usage
                step.set_model(
                    provider="openai-gpt4",
                    tokens_in=len(request.query.split()),
                    tokens_out=len(response_text.split())
                )
                
                # Estimate cost (10 cents for this example)
                step.set_cost(10)
                
                step.set_input(request.query[:300])
                step.set_output(response_text[:300])
            
            # Step 4: Post-process
            with telemetry.step("post_process", StepKind.SYSTEM) as step:
                final_result = response_text.upper()  # Simple transformation
                step.set_output(f"Processed {len(final_result)} chars")
            
            # Telemetry automatically sent here on context exit
            # with 'verified' badge
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return InvokeResponse(
                result=final_result,
                execution_time_ms=execution_time_ms,
                trace_id=telemetry.builder.trace_id,
                invocation_id=telemetry.builder.invocation_id,
                telemetry_status="verified"
            )
    
    except Exception as e:
        # Error handling - telemetry automatically marked as ERROR
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        client.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "example-external-agent"}


@app.post("/register")
async def register_with_agentos():
    """
    Register this agent with AgentOS platform.
    
    Call this once to register your agent as Model B.
    """
    agentos_base_url = os.getenv("AGENTOS_URL", "http://localhost:8000")
    agentos_api_key = os.getenv("AGENTOS_API_KEY", "demo-key")
    owner_id = os.getenv("AGENTOS_OWNER_ID", "user-demo")
    
    agent_endpoint = os.getenv("AGENT_ENDPOINT", "http://localhost:8001/invoke")
    
    with AgentOSClient(
        base_url=agentos_base_url,
        api_key=agentos_api_key
    ) as client:
        
        result = client.register_agent(
            name="example-external-agent",
            endpoint=agent_endpoint,
            owner_id=owner_id,
            description="Example external agent with SDK integration",
            metadata={
                "framework": "custom",
                "version": "1.0.0",
                "capabilities": ["qa", "summarization"],
                "sdk_version": "0.1.0"
            }
        )
        
        return {
            "status": "registered",
            "agent_id": result.get("agent_id"),
            "message": "Agent successfully registered with AgentOS",
            "telemetry_quality": "verified"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
