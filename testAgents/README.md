# AgentOS Test Agents

Sample agents demonstrating both Model A and Model B patterns.

## 📁 Contents

### `model_a_sample/` - Calculator Agent
**Model A**: Code-based agent that runs on AgentOS infrastructure

- ✅ Complete working example
- ✅ Local testing included
- ✅ Registration & invocation scripts
- ✅ ATP v0 telemetry
- ✅ Full documentation

**Quick Start:**
```bash
cd model_a_sample
python test_local.py              # Test locally
./register_agent.sh               # Deploy to AgentOS
./invoke_agent.sh <agent-id>      # Invoke deployed agent
```

### `model_b_sample.py` - Meal Planning Agent
**Model B**: External endpoint agent (your infrastructure)

- ✅ FastAPI wrapper for Streamlit agent
- ✅ Gemini 2.0 integration
- ✅ ATP v0 telemetry
- ✅ Health check endpoint

**Quick Start:**
```bash
python model_b_sample.py          # Start wrapper on port 9001
# Then register endpoint with AgentOS (see QUICKSTART.md)
```

### Supporting Files

- `QUICKSTART.md` - Quick reference for both models
- `test_wrapper.sh` - Test Model B wrapper
- `test.md` - Your custom test commands

## 🚀 Getting Started

### 1. Choose Your Agent Type

**Use Model A if:**
- Building new Python agents
- Want automatic scaling
- Need built-in deployment
- Rapid development

**Use Model B if:**
- Have existing service/API
- Need non-Python runtime
- Want full infrastructure control
- Service runs elsewhere

### 2. Test Locally

**Model A:**
```bash
cd model_a_sample
python test_local.py
```

**Model B:**
```bash
python model_b_sample.py
# In another terminal:
./test_wrapper.sh
```

### 3. Deploy to AgentOS

**Model A:**
```bash
cd model_a_sample
./register_agent.sh
# Save the agent ID
```

**Model B:**
```bash
# Keep wrapper running, then:
curl -X POST "http://localhost:8082/v1/agents/modelB" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "meal-planner",
    "endpoint_url": "http://host.docker.internal:9001/invoke",
    "auth_config": {"type": "none"}
  }'
```

### 4. Invoke & Monitor

```bash
# Model A
cd model_a_sample
./invoke_agent.sh <agent-id>

# Model B  
curl -X POST "http://localhost:8082/v1/agents/<agent-id>/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"input_data": {"prompt": "Quick breakfast"}}'

# View in UI
open http://localhost:3001
```

## 📊 Monitoring

### Web UI
- **Agents**: `http://localhost:3001/agents`
- **Invocations**: `http://localhost:3001/invocations`
- **Traces**: Click "View Trace" on any invocation

### API
```bash
# List agents
curl "http://localhost:8082/v1/observability/agents" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'

# View invocations
curl "http://localhost:8082/v1/observability/agents/invocations" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

## 🔧 Development

### Modify Model A Agent

1. Edit `model_a_sample/agent.py`
2. Test: `python test_local.py`
3. Re-deploy: `./register_agent.sh`

### Modify Model B Agent

1. Edit `model_b_sample.py`
2. Restart: `python model_b_sample.py`
3. No re-registration needed!

## 📚 Documentation

- **Model A Details**: `model_a_sample/README.md`
- **Quick Reference**: `QUICKSTART.md`
- **Architecture**: `../docs/ARCHITECTURE.md`
- **API Reference**: `../docs/API.md`

## 🎯 Features Demonstrated

### Both Models
- ✅ ATP v0 telemetry
- ✅ Cost tracking
- ✅ Error handling
- ✅ JWT authentication
- ✅ Invocation tracking
- ✅ UI integration

### Model A Specific
- ✅ Code upload
- ✅ Automatic building
- ✅ Container execution
- ✅ Dependency management

### Model B Specific
- ✅ External endpoint
- ✅ Custom runtime
- ✅ Health checks
- ✅ Manual telemetry

## 🐛 Troubleshooting

### Agent Not Showing in UI

1. Refresh browser
2. Check browser console
3. Verify services running:
   ```bash
   docker ps
   ```

### Build Failed (Model A)

```bash
docker logs agentos_runtime_1 --tail 50
```

### Connection Refused (Model B)

```bash
# Check if wrapper is running
curl http://localhost:9001/health
```

## 💡 Next Steps

1. ✅ Run both sample agents
2. 📝 Modify for your use case
3. 🔄 Add more operations/features
4. 📊 Monitor in UI
5. 🚀 Deploy to production

## 🤝 Support

- Check docs: `../docs/`
- View logs: `docker logs <service-name>`
- Test API: Use curl commands in `QUICKSTART.md`
