# 🍽️ Meal Planning Agent - AgentOS Integration

## Overview

This directory contains everything needed to integrate the **Meal Planning Agent** (originally a Streamlit app) with **AgentOS as a Model B external agent**.

### What's Included

| File | Purpose |
|------|---------|
| `agent.py` | Original Streamlit agent with meal planning logic |
| `model_b_sample.py` | **FastAPI wrapper for AgentOS integration** ⭐ |
| `INTEGRATION_GUIDE.md` | **Complete step-by-step integration guide** ⭐ |
| `PROBLEM_AND_SOLUTION.md` | Explains why Streamlit can't connect directly |
| `test_wrapper.sh` | Quick test script for the FastAPI wrapper |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

## Quick Start (3 Steps)

### 1️⃣ Setup

```bash
cd /Users/upalc/AgentOS/agentos/testAgents

# Copy and edit .env with your API keys
cp .env.example .env
# Add your GOOGLE_API_KEY or GEMINI_API_KEY

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Start the Wrapper

```bash
python model_b_sample.py
```

You should see:
```
🚀 Initializing Meal Planning Agent...
✅ Agent initialized successfully!
INFO:     Uvicorn running on http://0.0.0.0:9000
```

### 3️⃣ Test It

```bash
./test_wrapper.sh
```

Expected output:
```
🧪 Testing Meal Planning Agent FastAPI Wrapper
==============================================

1. Checking if wrapper is running...
✓ Wrapper is running

2. Testing health check...
✓ Health check passed

3. Testing agent invocation...
✓ Invocation successful

4. Verifying telemetry...
✓ Telemetry quality: verified

✓ All tests passed!
```

## Register with AgentOS

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
    "timeout_seconds": 30
  }'
```

**Save the `agent_id` from the response!**

## Invoke via AgentOS

```bash
curl -X POST http://localhost:8082/v1/agents/YOUR_AGENT_ID/invoke \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "prompt": "Create a vegetarian meal plan for 2 people for 3 days"
    },
    "timeout": 30
  }'
```

## View in AgentOS UI

Open http://localhost:3001 and:

1. **Dashboard** → See agent with "Verified Telemetry" badge ✅
2. **Agents** → View agent details and status
3. **Logs** → Filter by agent_id to see invocation logs
4. **Trace Viewer** → Click invocation for step-by-step breakdown

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Your System                       │
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  Streamlit   │         │   FastAPI    │         │
│  │   :8501      │◄────────┤  Wrapper     │         │
│  │              │         │   :9000      │         │
│  │ (Human UI)   │         │ (AgentOS API)│         │
│  └──────────────┘         └──────┬───────┘         │
│                                   │                  │
│                                   │                  │
│                            ┌──────▼───────┐         │
│                            │ Agent Logic  │         │
│                            │  (agent.py)  │         │
│                            └──────────────┘         │
└─────────────────────────────────────────────────────┘
                                   ▲
                                   │
                                   │ HTTP/JSON
                                   │
                    ┌──────────────┴──────────────┐
                    │      AgentOS Runtime        │
                    │        :8082                │
                    └─────────────────────────────┘
```

**Key Points:**
- Both Streamlit and FastAPI can run simultaneously
- Humans use Streamlit for interactive chat
- AgentOS uses FastAPI wrapper for automation
- Both share the same agent logic from `agent.py`

## Why You Need the Wrapper

❌ **Streamlit Can't Work Directly** because:
- Serves HTML/WebSocket traffic, not JSON
- No `/invoke` endpoint that accepts POST requests
- Not designed for programmatic access

✅ **FastAPI Wrapper Solves This** by:
- Exposing `/invoke` endpoint with JSON
- Returning structured responses with telemetry
- Providing `/health` for monitoring
- Enabling AgentOS "verified telemetry" badge

## What Gets Logged in AgentOS

Every invocation logs:
- 📊 Execution time (milliseconds)
- 📝 Input prompt and output response (excerpts)
- ✅ Success/error status
- 🏷️ Model used (gemini-2.0-flash-exp)
- 🔍 Step-by-step execution trace
- ⏰ Timestamps (start/end)
- 💰 Cost tracking (if configured)

## API Endpoints

### POST /invoke
Invoke the meal planning agent.

**Request:**
```json
{
  "prompt": "Suggest a healthy dinner for two",
  "timeout": 30
}
```

**Response:**
```json
{
  "output": "Here are some healthy dinner ideas...",
  "execution_time_ms": 1234,
  "timestamp": "2025-11-01T12:00:00.000Z",
  "metadata": {
    "model": "gemini-2.0-flash-exp",
    "prompt_length": 33,
    "response_length": 450
  },
  "telemetry": {
    "trace_id": "trace_1234567890",
    "status": "success",
    "steps": [...],
    "metadata": {
      "telemetry_quality": "verified"
    }
  }
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "timestamp": "2025-11-01T12:00:00.000Z"
}
```

## Troubleshooting

### Wrapper Won't Start

**Error:** `ModuleNotFoundError: No module named 'agno'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Health Check Fails

**Error:** `curl: (7) Failed to connect to localhost port 9000`

**Solution:**
- Check if wrapper is running: `ps aux | grep model_b_sample`
- Check for port conflicts: `lsof -i :9000`
- Look for errors in console output

### Registration Shows "Unhealthy"

**Error:** Agent registered but shows "unhealthy" status

**Solution:**
- Use `http://host.docker.internal:9000` not `http://localhost:9000`
- Verify health check works: `curl http://localhost:9000/health`
- Check Docker can reach your host machine

### Missing API Key

**Error:** `GOOGLE_API_KEY not found`

**Solution:**
```bash
# Edit .env file
echo "GOOGLE_API_KEY=your-key-here" >> .env

# Restart wrapper
python model_b_sample.py
```

## Environment Variables

Required:
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - For the LLM

Optional:
- `SPOONACULAR_API_KEY` - For recipe search features

## Features

The agent can help with:
- 🔍 **Recipe Discovery** - Search recipes by ingredients
- 📊 **Nutrition Analysis** - Get nutritional breakdowns
- 💰 **Cost Estimation** - Calculate meal costs with budget tips
- 📅 **Meal Planning** - Generate weekly meal plans with shopping lists

## Example Prompts

Try these through AgentOS:

```bash
# Quick breakfast idea
"Give me a quick healthy breakfast idea"

# Recipe search
"Find recipes using chicken, broccoli, and rice"

# Nutrition analysis
"What's the nutritional value of chicken teriyaki?"

# Meal planning
"Create a vegetarian meal plan for 2 people for 5 days with a moderate budget"

# Cost estimation
"Estimate the cost of making pasta with tomatoes, basil, and mozzarella for 4 people"
```

## Next Steps

1. ✅ Test locally with `./test_wrapper.sh`
2. ✅ Register with AgentOS
3. ✅ Invoke through AgentOS
4. ✅ View telemetry in UI
5. 📊 Set up monitoring and alerts
6. 🔐 Configure authentication for production
7. 🚀 Deploy with proper scaling

## Documentation

- **Quick Start:** This file
- **Detailed Guide:** `INTEGRATION_GUIDE.md`
- **Problem Explanation:** `PROBLEM_AND_SOLUTION.md`
- **Original App:** `agent.py` (Streamlit)

## Support

For issues or questions:
1. Check `PROBLEM_AND_SOLUTION.md` for common issues
2. Review `INTEGRATION_GUIDE.md` for detailed steps
3. Run `./test_wrapper.sh` to diagnose problems
4. Check AgentOS logs: `docker logs agentos_runtime_1`

---

**Ready to integrate?** Start with `./test_wrapper.sh` and follow `INTEGRATION_GUIDE.md`! 🚀
