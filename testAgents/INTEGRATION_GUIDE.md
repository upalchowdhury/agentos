# Integrating Your Meal Planning Agent with AgentOS

## Why You Need an HTTP Wrapper

**The Problem:** Your `agent.py` is a Streamlit app that serves HTML/WebSocket traffic. AgentOS can only communicate with HTTP APIs that accept JSON requests and return JSON responses.

**The Solution:** `model_b_sample.py` is a FastAPI wrapper that:
- Imports your agent logic from `agent.py`
- Exposes `/invoke` endpoint that accepts JSON
- Returns structured JSON responses
- Includes AgentOS telemetry for verified tracking

You can keep both running:
- **Streamlit** (`agent.py`) → Human interaction at http://localhost:8501
- **FastAPI wrapper** (`model_b_sample.py`) → AgentOS automation at http://localhost:9000

---

## Step-by-Step Integration

### Step 1: Set Up Environment Variables

Create `/Users/upalc/AgentOS/agentos/testAgents/.env`:

```bash
# Required for the agent to work
GOOGLE_API_KEY=your-google-api-key-here
# OR
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: For recipe search features
SPOONACULAR_API_KEY=your-spoonacular-key-here
```

### Step 2: Install Dependencies

```bash
cd /Users/upalc/AgentOS
pip install -r agentos/testAgents/requirements.txt
```

This installs: `fastapi`, `uvicorn`, `streamlit`, `agno`, `python-dotenv`, etc.

### Step 3: Start the HTTP Wrapper

```bash
cd /Users/upalc/AgentOS/agentos/testAgents
python model_b_sample.py
```

**Expected output:**
```
🚀 Initializing Meal Planning Agent...
✅ Agent initialized successfully!
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

**Verify it's working:**
```bash
# Health check
curl http://localhost:9000/health

# Test invocation
curl -X POST http://localhost:9000/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a healthy dinner for two"}'
```

### Step 4: Register with AgentOS

**Option A: Direct to Runtime Service (Recommended for testing)**

```bash
curl -X POST http://localhost:8082/v1/agents/modelB \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "meal-planner",
    "endpoint_url": "http://host.docker.internal:9000/invoke",
    "auth": {"type": "none"},
    "rate_limit": {"rps": 5, "burst": 10},
    "health_check_path": "/health",
    "timeout_seconds": 30,
    "alerts": {
      "error_rate": 0.5,
      "latency_ms": 5000
    }
  }'
```

**Important:** Use `http://host.docker.internal:9000` instead of `http://localhost:9000` so Docker containers can reach your local machine.

**Save the `agent_id` from the response!**

**Option B: Through Gateway (requires valid JWT)**

```bash
# First, create a DID and get credentials
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{"agentType": "admin", "metadata": {"name": "Test User"}}'

# Then issue a credential (save the token)
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{"subjectDID": "YOUR_DID_HERE", "claims": {"role": "admin"}, "expiresIn": "30d"}'

# Now register through gateway
curl -X POST http://localhost:8080/v1/agents/modelB \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{...same payload as above...}'
```

### Step 5: Invoke Through AgentOS

**Direct to Runtime:**
```bash
curl -X POST "http://localhost:8082/v1/agents/YOUR_AGENT_ID/invoke" \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "prompt": "Create a vegetarian meal plan for 2 people for 3 days"
    },
    "timeout": 30
  }'
```

**Through Gateway (with valid token):**
```bash
curl -X POST "http://localhost:8080/v1/agents/YOUR_AGENT_ID/invoke" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...same as above...}'
```

### Step 6: View in AgentOS UI

Open http://localhost:3001:

1. **Dashboard** → See your agent with "Verified Telemetry" badge
2. **Agents** → View agent details, status, invocation count
3. **Logs** → Filter by agent_id to see invocation logs
4. **Trace Viewer** → Click an invocation to see step-by-step execution
5. **Export Audit** → Download CSV with full audit trail

---

## Troubleshooting

### Agent Won't Start

**Problem:** `Failed to initialize agent: No module named 'agno'`

**Solution:**
```bash
pip install agno google-genai python-dotenv
```

### Health Check Fails

**Problem:** `curl http://localhost:9000/health` returns connection refused

**Solution:**
- Ensure `model_b_sample.py` is running
- Check for port conflicts: `lsof -i :9000`
- Look for startup errors in console

### Registration Fails

**Problem:** `"endpoint_url": "http://localhost:9000/invoke"` gives "unhealthy" status

**Solution:**
- Use `http://host.docker.internal:9000/invoke` for Docker environments
- Verify the agent is accessible: `curl http://host.docker.internal:9000/health`

### Invocation Times Out

**Problem:** Agent invocation returns timeout error

**Solution:**
- Increase timeout in invoke request: `"timeout": 60`
- Check agent logs for errors
- Verify API keys are set correctly in `.env`

### No Telemetry in UI

**Problem:** Agent shows "Partial Telemetry" instead of "Verified"

**Solution:**
- Ensure `model_b_sample.py` is returning the `telemetry` field
- Check response includes `telemetry_quality: "verified"`
- Invoke the agent at least once to trigger telemetry upgrade

---

## Architecture Diagram

```
┌─────────────┐
│   Human     │
│  (Browser)  │
└──────┬──────┘
       │
       ├─────────────────────┐
       │                     │
       v                     v
┌──────────────┐      ┌─────────────┐
│  Streamlit   │      │  AgentOS    │
│   :8501      │      │   UI :3001  │
└──────────────┘      └──────┬──────┘
                              │
                              v
                       ┌──────────────┐
                       │   Gateway    │
                       │    :8080     │
                       └──────┬───────┘
                              │
                              v
                       ┌──────────────┐
                       │   Runtime    │
                       │    :8082     │
                       └──────┬───────┘
                              │
                              v
                       ┌──────────────┐
                       │   FastAPI    │
                       │ Wrapper :9000│
                       └──────┬───────┘
                              │
                              v
                       ┌──────────────┐
                       │  Agent Logic │
                       │  (agent.py)  │
                       └──────────────┘
```

---

## What Gets Logged

Each invocation logs:
- ✅ Invocation ID and trace ID
- ✅ Input prompt and output response
- ✅ Execution time (ms)
- ✅ Model used (gemini-2.0-flash-exp)
- ✅ Status (success/error)
- ✅ Timestamp
- ✅ Step-by-step execution trace
- ✅ Error messages (if any)

All this data is available in:
- Dashboard (aggregated metrics)
- Logs page (filterable log entries)
- Trace Viewer (detailed step breakdown)
- Audit Export (CSV download for compliance)

---

## Next Steps

1. ✅ Test the wrapper locally: `python model_b_sample.py`
2. ✅ Register with AgentOS
3. ✅ Invoke through AgentOS
4. ✅ View telemetry in UI
5. 🚀 Deploy to production with proper auth
6. 📊 Set up monitoring dashboards
7. 🔐 Configure policy rules and rate limits
