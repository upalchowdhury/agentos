"""
Model A Sample Agent: Simple Calculator Agent
Demonstrates AgentOS Model A pattern with ATP v0 telemetry
"""
import json
import time
from datetime import datetime
from typing import Any, Dict


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    AgentOS Model A entry point
    
    Args:
        event: {
            "input_data": dict,  # User input
            "context": dict      # AgentOS context (invocation_id, agent_id, etc.)
        }
    
    Returns:
        {
            "result": dict,      # Agent output
            "telemetry": dict,   # ATP v0 telemetry trace
            "cost": float        # Cost in USD
        }
    """
    start_time = time.time()
    
    # Extract input
    input_data = event.get("input_data", {})
    context = event.get("context", {})
    
    operation = input_data.get("operation", "add")
    numbers = input_data.get("numbers", [])
    
    # Validate input
    if not numbers or not isinstance(numbers, list):
        return {
            "result": {"error": "Invalid input: 'numbers' must be a non-empty list"},
            "telemetry": None,
            "cost": 0.0
        }
    
    # Perform calculation
    try:
        if operation == "add":
            result_value = sum(numbers)
        elif operation == "multiply":
            result_value = 1
            for n in numbers:
                result_value *= n
        elif operation == "average":
            result_value = sum(numbers) / len(numbers)
        else:
            result_value = None
            error = f"Unknown operation: {operation}"
    except Exception as e:
        return {
            "result": {"error": f"Calculation failed: {str(e)}"},
            "telemetry": None,
            "cost": 0.0
        }
    
    end_time = time.time()
    execution_ms = int((end_time - start_time) * 1000)
    
    # Build result
    output = {
        "operation": operation,
        "numbers": numbers,
        "result": result_value,
        "executed_at": datetime.utcnow().isoformat()
    }
    
    # ATP v0 Telemetry
    telemetry = {
        "trace": {
            "trace_id": context.get("invocation_id", "local-trace"),
            "agent_id": context.get("agent_id", "unknown"),
            "status": "SUCCESS",
            "start_ts": datetime.utcfromtimestamp(start_time).isoformat(),
            "end_ts": datetime.utcfromtimestamp(end_time).isoformat(),
            "execution_time_ms": execution_ms,
            "steps": [
                {
                    "step_id": f"{context.get('invocation_id', 'local')}-calc",
                    "parent_step_id": None,
                    "name": "calculate",
                    "kind": "tool",
                    "start_ts": datetime.utcfromtimestamp(start_time).isoformat(),
                    "end_ts": datetime.utcfromtimestamp(end_time).isoformat(),
                    "latency_ms": execution_ms,
                    "status": "SUCCESS",
                    "input_excerpt": f"{operation}({numbers})",
                    "output_excerpt": str(result_value)[:100]
                }
            ]
        }
    }
    
    # Calculate cost (example: $0.0001 per operation)
    cost = 0.0001
    
    return {
        "result": output,
        "telemetry": telemetry,
        "cost": cost
    }


# Local testing
if __name__ == "__main__":
    # Test the handler locally
    test_event = {
        "input_data": {
            "operation": "add",
            "numbers": [10, 20, 30]
        },
        "context": {
            "invocation_id": "local-test-123",
            "agent_id": "calculator-agent"
        }
    }
    
    result = handler(test_event)
    print(json.dumps(result, indent=2))
