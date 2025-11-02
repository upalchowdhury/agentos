"""
Simple Calculator Agent - Optimized for UI Deployment
Paste this directly into the AgentOS UI "Deploy Agent" form

No dependencies required - just paste and deploy!
"""

def handler(event):
    """
    Calculate math operations
    
    Input: {
        "operation": "add|multiply|average",
        "numbers": [1, 2, 3, ...]
    }
    """
    # Extract input
    input_data = event.get("input_data", {})
    operation = input_data.get("operation", "add")
    numbers = input_data.get("numbers", [])
    
    # Validate
    if not numbers or not isinstance(numbers, list):
        return {
            "result": {"error": "Invalid input: 'numbers' must be a non-empty list"},
            "cost": 0.0
        }
    
    # Calculate
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
            return {
                "result": {"error": f"Unknown operation: {operation}"},
                "cost": 0.0
            }
    except Exception as e:
        return {
            "result": {"error": f"Calculation failed: {str(e)}"},
            "cost": 0.0
        }
    
    # Return result
    return {
        "result": {
            "operation": operation,
            "numbers": numbers,
            "result": result_value
        },
        "cost": 0.0001
    }
