# Model A Sample Agent: Calculator

A simple calculator agent demonstrating the AgentOS Model A pattern. This agent performs basic mathematical operations (addition, multiplication, averaging) and includes proper ATP v0 telemetry.

## Overview

**Model A** agents run code on AgentOS infrastructure:
- Code is uploaded and built by AgentOS
- Executed in isolated containers
- Full telemetry and cost tracking
- Automatic scaling and resource management

## 🚀 Two Deployment Methods

### Method 1: UI Deployment (Quickest) ⭐

**Best for**: Quick testing, single-file agents

```bash
# 1. Open UI: http://localhost:3001
# 2. Click "Deploy Code (Model A)"
# 3. Paste code from agent_ui_simple.py
# 4. Click "Deploy Agent"
```

📖 **[Full UI Deployment Guide →](UI_DEPLOYMENT_GUIDE.md)**

### Method 2: Script Deployment (Production)

**Best for**: Production, dependencies, automation

```bash
# 1. Test locally
python test_local.py

# 2. Deploy via script
./register_agent.sh

# 3. Test deployed agent
./invoke_agent.sh <agent-id>
```

## Agent Structure

```
model_a_sample/
├── agent.py              # Main agent handler
├── requirements.txt      # Python dependencies
├── register_agent.sh     # Registration script
├── invoke_agent.sh       # Invocation script
├── test_local.py         # Local testing
└── README.md            # This file
```

## Quick Start

### 1. Test Locally

Before deploying, test the agent locally:

```bash
# Run local tests
python test_local.py

# Or test the handler directly
python agent.py
```

### 2. Register Agent with AgentOS

```bash
# Make scripts executable
chmod +x register_agent.sh invoke_agent.sh

# Register the agent
./register_agent.sh
```

This will:
1. Create the agent in AgentOS
2. Package your code (agent.py + requirements.txt)
3. Upload the code artifact
4. Wait for the build to complete
5. Return your agent ID

**Save the agent ID** - you'll need it for invocations!

### 3. Invoke the Agent

```bash
# Replace with your actual agent ID
./invoke_agent.sh <your-agent-id>
```

## Agent Code Structure

### Handler Function

```python
def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    AgentOS Model A entry point
    
    Args:
        event: {
            "input_data": dict,  # User input
            "context": dict      # AgentOS context
        }
    
    Returns:
        {
            "result": dict,      # Your output
            "telemetry": dict,   # ATP v0 telemetry
            "cost": float        # Cost in USD
        }
    """
```

### Input Format

```json
{
  "input_data": {
    "operation": "add",
    "numbers": [10, 20, 30]
  }
}
```

### Output Format

```json
{
  "result": {
    "operation": "add",
    "numbers": [10, 20, 30],
    "result": 60,
    "executed_at": "2025-11-01T21:00:00"
  },
  "telemetry": {
    "trace": {
      "trace_id": "...",
      "status": "SUCCESS",
      "execution_time_ms": 5
    }
  },
  "cost": 0.0001
}
```

## Supported Operations

1. **Addition** - Sum all numbers
   ```json
   {"operation": "add", "numbers": [10, 20, 30]}
   → Result: 60
   ```

2. **Multiplication** - Multiply all numbers
   ```json
   {"operation": "multiply", "numbers": [5, 3, 2]}
   → Result: 30
   ```

3. **Average** - Calculate average
   ```json
   {"operation": "average", "numbers": [100, 200, 300]}
   → Result: 200.0
   ```

## Monitoring

### View in UI

1. **Agents Page**: `http://localhost:3001/agents`
   - See agent status, type (A), invocation count
   
2. **Invocations Page**: `http://localhost:3001/invocations`
   - View all invocations with execution times
   - Click "View Trace" for detailed telemetry

### API Queries

```bash
# Get agent details
curl -s "http://localhost:8082/v1/agents/<agent-id>" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'

# Get recent invocations
curl -s "http://localhost:8082/v1/observability/agents/invocations?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'

# Get build status
curl -s "http://localhost:8082/v1/agents/<agent-id>/build" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

## Development Tips

### Adding Dependencies

Edit `requirements.txt`:
```
numpy==1.24.0
requests==2.31.0
```

### Testing Changes

1. Make code changes
2. Test locally: `python test_local.py`
3. Re-upload: `./register_agent.sh` (it will update the existing agent)

### Debugging

Check runtime logs:
```bash
docker logs agentos_runtime_1 --tail 50 -f
```

## ATP v0 Telemetry

This agent includes proper ATP v0 telemetry:

```python
telemetry = {
    "trace": {
        "trace_id": "...",
        "agent_id": "...",
        "status": "SUCCESS",
        "start_ts": "...",
        "end_ts": "...",
        "execution_time_ms": 123,
        "steps": [
            {
                "step_id": "...",
                "name": "calculate",
                "kind": "tool",
                "status": "SUCCESS",
                "latency_ms": 123,
                "input_excerpt": "add([10,20,30])",
                "output_excerpt": "60"
            }
        ]
    }
}
```

This enables:
- Detailed execution tracing
- Performance monitoring
- Cost attribution
- Debugging and optimization

## Model A vs Model B

| Feature | Model A (This Example) | Model B (External) |
|---------|------------------------|-------------------|
| Hosting | AgentOS infrastructure | Your infrastructure |
| Deployment | Upload code | Register endpoint |
| Scaling | Automatic | Manual |
| Telemetry | Built-in | Manual integration |
| Best For | Python agents, rapid dev | Existing services, any language |

## Next Steps

1. **Modify the agent** - Add your own logic to `agent.py`
2. **Add more operations** - Extend the calculator
3. **Use external APIs** - Add requests to `requirements.txt`
4. **Add more telemetry** - Track individual steps
5. **Deploy to production** - Update JWT token and URLs

## Troubleshooting

### Build Failed

Check build logs:
```bash
docker logs agentos_runtime_1 | grep -A 20 "build"
```

Common issues:
- Missing dependencies in `requirements.txt`
- Syntax errors in `agent.py`
- Import errors

### Invocation Errors

Check if agent is RUNNING:
```bash
curl -s "http://localhost:8082/v1/agents/<agent-id>" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.status'
```

### Agent Not Visible in UI

1. Refresh the page
2. Check browser console for errors
3. Verify runtime service is running:
   ```bash
   docker ps | grep runtime
   ```

## Support

- Documentation: `/agentos/docs/`
- Architecture: `/agentos/docs/ARCHITECTURE.md`
- API Reference: `/agentos/docs/API.md`
