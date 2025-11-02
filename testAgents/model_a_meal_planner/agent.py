"""
Meal Planning Agent - Model A Version
Uses Gemini 2.0 Flash for meal planning with full ATP v0 telemetry
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Dict

# Google Generative AI
import google.generativeai as genai


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    AgentOS Model A handler for meal planning
    
    Args:
        event: {
            "input_data": {"prompt": "user query"},
            "context": {"invocation_id": "...", "agent_id": "..."}
        }
    
    Returns:
        {
            "result": dict,
            "telemetry": dict,
            "cost": float
        }
    """
    start_time = time.time()
    
    # Extract input
    input_data = event.get("input_data", {})
    context = event.get("context", {})
    
    # Get prompt
    if isinstance(input_data, dict):
        prompt = input_data.get("prompt", "")
    else:
        prompt = str(input_data)
    
    if not prompt:
        return {
            "result": {"error": "No prompt provided"},
            "telemetry": None,
            "cost": 0.0
        }
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "result": {"error": "GOOGLE_API_KEY not set in environment"},
            "telemetry": None,
            "cost": 0.0
        }
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    try:
        # Call Gemini
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        system_prompt = """You are a helpful meal planning assistant. 
Provide practical, healthy meal suggestions with brief recipes when appropriate.
Be concise but helpful."""
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        response = model.generate_content(full_prompt)
        output_text = response.text
        
    except Exception as e:
        return {
            "result": {"error": f"Gemini API error: {str(e)}"},
            "telemetry": None,
            "cost": 0.0
        }
    
    end_time = time.time()
    execution_ms = int((end_time - start_time) * 1000)
    
    # Build result
    result_data = {
        "response": output_text,
        "prompt": prompt,
        "model": "gemini-2.0-flash-exp",
        "executed_at": datetime.utcnow().isoformat()
    }
    
    # ATP v0 Telemetry
    trace_id = context.get("invocation_id", "local-trace")
    telemetry = {
        "trace": {
            "trace_id": trace_id,
            "agent_id": context.get("agent_id", "meal-planner"),
            "status": "SUCCESS",
            "start_ts": datetime.utcfromtimestamp(start_time).isoformat(),
            "end_ts": datetime.utcfromtimestamp(end_time).isoformat(),
            "execution_time_ms": execution_ms,
            "steps": [
                {
                    "step_id": f"{trace_id}-gemini-call",
                    "parent_step_id": None,
                    "name": "gemini.generate_content",
                    "kind": "llm",
                    "start_ts": datetime.utcfromtimestamp(start_time).isoformat(),
                    "end_ts": datetime.utcfromtimestamp(end_time).isoformat(),
                    "latency_ms": execution_ms,
                    "status": "SUCCESS",
                    "input_excerpt": prompt[:100],
                    "output_excerpt": output_text[:100],
                    "model_provider": "google",
                    "tokens_in": len(prompt.split()),
                    "tokens_out": len(output_text.split())
                }
            ]
        }
    }
    
    # Estimate cost (Gemini 2.0 Flash is ~$0.075 per 1M input tokens)
    estimated_tokens = len(prompt.split()) + len(output_text.split())
    cost = (estimated_tokens / 1_000_000) * 0.075
    
    return {
        "result": result_data,
        "telemetry": telemetry,
        "cost": cost
    }


# Local testing
if __name__ == "__main__":
    # Test the handler locally
    test_event = {
        "input_data": {
            "prompt": "Suggest a quick healthy breakfast for one person"
        },
        "context": {
            "invocation_id": "local-test-001",
            "agent_id": "meal-planner"
        }
    }
    
    print("Testing Meal Planner Agent...")
    print("=" * 60)
    
    result = handler(test_event)
    
    if "error" in result.get("result", {}):
        print(f"❌ Error: {result['result']['error']}")
    else:
        print(f"✅ Response: {result['result']['response'][:200]}...")
        print(f"⏱️  Execution: {result['telemetry']['trace']['execution_time_ms']}ms")
        print(f"💰 Cost: ${result['cost']:.6f}")
