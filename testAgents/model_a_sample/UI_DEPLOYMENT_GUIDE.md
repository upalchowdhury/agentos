# UI Deployment Guide - Model A Agent

Step-by-step guide to deploy the calculator agent using the AgentOS Web UI.

## 📋 Prerequisites

1. AgentOS is running: `docker ps` (should show all services)
2. UI is accessible: `http://localhost:3001`
3. You have authentication set up (localStorage token)

## 🚀 Deployment Steps

### Step 1: Open Deploy Page

1. Go to `http://localhost:3001`
2. Click **"Deploy Code (Model A)"** button
   - Or navigate to the Agents page and click the blue "Deploy Code" button

### Step 2: Copy the Agent Code

Open `agent_ui_simple.py` in this folder and **copy the entire content**.

Or copy this:

```python
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
```

### Step 3: Fill in the Form

**Agent ID**: `calculator-agent` (or your preferred name)

**Agent Code**: Paste the code from Step 2

**Max Memory**: `512 MB` (default is fine)

**Max CPU**: `0.5 cores` (default is fine)

### Step 4: Deploy

Click the **"Deploy Agent"** button at the bottom

### Step 5: Wait for Build

The agent will:
1. ✅ Be created
2. ✅ Code uploaded
3. ✅ Built into container
4. ✅ Status changes to RUNNING

This takes about 10-30 seconds.

## 🧪 Testing Your Agent

### Method 1: Using curl

Save your **agent_id** from the deployment, then:

```bash
# Replace <agent-id> with your actual ID
export AGENT_ID="<agent-id>"
export JWT_TOKEN="eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Ijp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA"

# Test 1: Addition
curl -X POST "http://localhost:8082/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "add",
      "numbers": [10, 20, 30]
    }
  }' | jq '.'

# Test 2: Multiplication
curl -X POST "http://localhost:8082/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "multiply",
      "numbers": [5, 3, 2]
    }
  }' | jq '.'

# Test 3: Average
curl -X POST "http://localhost:8082/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "average",
      "numbers": [100, 200, 300]
    }
  }' | jq '.'
```

### Method 2: Using the UI

1. Go to **Agents** page
2. Find your `calculator-agent`
3. Click **"View Details"**
4. Use the invoke form (if available)

### Expected Results

**Addition (10 + 20 + 30):**
```json
{
  "status": "SUCCESS",
  "result": {
    "operation": "add",
    "numbers": [10, 20, 30],
    "result": 60
  },
  "cost": 0.0001
}
```

**Multiplication (5 × 3 × 2):**
```json
{
  "status": "SUCCESS",
  "result": {
    "operation": "multiply",
    "numbers": [5, 3, 2],
    "result": 30
  },
  "cost": 0.0001
}
```

**Average ((100 + 200 + 300) / 3):**
```json
{
  "status": "SUCCESS",
  "result": {
    "operation": "average",
    "numbers": [100, 200, 300],
    "result": 200.0
  },
  "cost": 0.0001
}
```

## 📊 Monitor Your Agent

### View in UI

1. **Agents Page** (`http://localhost:3001/agents`)
   - See agent status (should be RUNNING)
   - View total invocations
   - Check success rate

2. **Invocations Page** (`http://localhost:3001/invocations`)
   - See all your test invocations
   - View execution times
   - Check results

### API Queries

```bash
# Get agent details
curl -s "http://localhost:8082/v1/agents/$AGENT_ID" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'

# Get build status
curl -s "http://localhost:8082/v1/agents/$AGENT_ID/build" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'

# Get recent invocations for this agent
curl -s "http://localhost:8082/v1/observability/agents/invocations?agent_id=$AGENT_ID" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

## 🔧 Troubleshooting

### Agent Status is "BUILDING" for too long

Check runtime logs:
```bash
docker logs agentos_runtime_1 --tail 50
```

### Agent Status is "FAILED"

1. Check the build logs in runtime
2. Verify your code has no syntax errors
3. Make sure you pasted the complete code

### "Agent not found" when invoking

1. Verify the agent ID is correct
2. Check agent exists: Visit Agents page in UI
3. Ensure agent status is RUNNING

### Invocation returns error

1. Check the error message in the response
2. Verify input format matches examples
3. Test with exact examples provided above

## 🎯 What's Different from Script Method?

| Feature | UI Paste (This Method) | Script Upload |
|---------|----------------------|---------------|
| **Code** | Single handler function | Full file structure |
| **Telemetry** | Basic | ATP v0 traces |
| **Dependencies** | None (built-in only) | Full requirements.txt |
| **Testing** | After deployment | Before deployment |
| **Best For** | Quick prototypes | Production agents |

## ✨ Tips

1. **Keep it Simple**: UI deployment works best for single-file agents
2. **No Dependencies**: If you need external packages (numpy, requests, etc.), use the script method
3. **Test Quickly**: Great for rapid iteration and testing
4. **Version Control**: For production, use the script method with git

## 🚀 Next Steps

1. ✅ Deploy the calculator agent via UI
2. ✅ Test with the curl commands above
3. ✅ View results in the UI
4. 📝 Modify the code for your use case
5. 🔄 Re-deploy to see changes

## 💡 Want More Features?

For a production-ready version with:
- ATP v0 telemetry traces
- Local testing before deployment
- External dependencies
- Multiple files
- Automated deployment

Use the **script method** with `register_agent.sh` from the main folder!

## 📚 Related Files

- `agent_ui_simple.py` - The code you paste in UI (this simplified version)
- `agent.py` - Full version with telemetry (for script deployment)
- `README.md` - Complete documentation
- `../QUICKSTART.md` - Quick reference
