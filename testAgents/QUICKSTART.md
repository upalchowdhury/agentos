# AgentOS Testing Quick Start

Quick reference for testing both Model A and Model B agents.

## Model A: Code-Based Agent (Calculator)

**Location**: `model_a_sample/`

### Quick Test

```bash
cd model_a_sample

# 1. Test locally first
python test_local.py

# 2. Register with AgentOS
./register_agent.sh

# 3. Copy the agent ID from output, then invoke
./invoke_agent.sh <your-agent-id>
```

### What You'll See

- ✅ Agent builds and deploys automatically
- ✅ Code runs in isolated container
- ✅ Full telemetry tracking
- ✅ Visible in UI at `http://localhost:3001/agents`

---

## Model B: External Endpoint Agent (Meal Planner)

**Location**: `model_b_sample.py`

### Quick Test

```bash
# Terminal 1: Start the wrapper
python model_b_sample.py

# Terminal 2: Register agent (one time)
curl -X POST "http://localhost:8082/v1/agents/modelB" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "meal-planner",
    "description": "Meal planning with Gemini",
    "endpoint_url": "http://host.docker.internal:9001/invoke",
    "auth_config": {"type": "none"}
  }'

# Terminal 2: Invoke agent
curl -X POST "http://localhost:8082/v1/agents/<agent-id>/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"prompt": "Quick breakfast"}}'
```

### What You'll See

- ✅ Agent proxies to your external service
- ✅ Your service stays in control
- ✅ Telemetry captured from ATP v0
- ✅ Visible in UI at `http://localhost:3001/agents`

---

## Key Differences

| Feature | Model A | Model B |
|---------|---------|---------|
| **Deployment** | Upload code | Register URL |
| **Hosting** | AgentOS | Your infrastructure |
| **Runtime** | Python 3.11 | Any language |
| **Use Case** | New agents, rapid dev | Existing services |

---

## JWT Token

Get your token from Identity service:

```bash
# Request a JWT token
curl -X POST "http://localhost:3000/api/v1/credentials/request" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "did:agent:ba474460-f24b-48f3-926c-6fd948e201ac",
    "issuer_id": "did:agent:issuer",
    "permissions": ["register_agent", "invoke_agent"],
    "role": "admin"
  }'
```

Or use the development token in the scripts.

---

## View Results

### Web UI

```bash
open http://localhost:3001
```

- **Agents**: See all registered agents
- **Invocations**: View execution history
- **Traces**: Debug with detailed telemetry

### API

```bash
# List all agents
curl -s "http://localhost:8082/v1/observability/agents" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'

# Recent invocations
curl -s "http://localhost:8082/v1/observability/agents/invocations?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

---

## Troubleshooting

### Agent not showing in UI

1. Refresh browser
2. Clear localStorage: `localStorage.clear()` in console
3. Set token: `localStorage.setItem('token', 'test-token')`

### Model A build failed

```bash
# Check runtime logs
docker logs agentos_runtime_1 --tail 50
```

### Model B not responding

```bash
# Check if wrapper is running
curl http://localhost:9001/health

# If not, restart it
python model_b_sample.py
```

---

## Next Steps

1. ✅ Test both agent types
2. 📝 Modify the code to fit your use case
3. 🚀 Deploy your own agents
4. 📊 Monitor in the UI
5. 🔍 Use traces for debugging
