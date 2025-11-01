AgentOS can only talk to HTTP APIs that accept JSON requests and return JSON responses. The Streamlit app on http://localhost:8501/ is just a UI, so the runtime can’t invoke it directly—you need a small HTTP wrapper that calls the same agent logic and exposes a /invoke endpoint. I’ve already dropped a working example into the repo; here’s how to use it (or adapt it to your agent).

1. Copy your LLM keys into .env
Make sure agentos/testAgents/.env (or your shell) has the same keys you use for the Streamlit app:

OPENAI_API_KEY=sk-...
# or GEMINI_API_KEY/GOOGLE_API_KEY if you prefer Gemini
2. Install the sample dependencies once
cd /Users/upalc/AgentOS
pip install -r agentos/testAgents/requirements.txt
This installs fastapi, uvicorn, openai, etc.

3. Start the HTTP wrapper
The repo now includes agentos/testAgents/model_b_sample.py, a FastAPI service that returns a JSON answer + telemetry trace:

uvicorn agentos.testAgents.model_b_sample:app --host 0.0.0.0 --port 9000
You should see:

INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
Health check (optional):

curl http://localhost:9000/health
# {"status":"healthy"}
If you’d rather reuse the Streamlit agent logic, create a similar FastAPI file that imports create_agent() from agent.py, executes it once, and handles prompts inside /invoke; the structure is identical to model_b_sample.py.

4. Register it with AgentOS (Model B)
With the AgentOS stack up (make dev-up):

curl -X POST http://localhost:8080/v1/agents/modelB \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "mealplanner-http",
        "endpoint_url": "http://localhost:9000/invoke",
        "auth": {"type": "none"},
        "rate_limit": {"rps": 5, "burst": 10},
        "health_check_path": "/health",
        "alerts": {"error_rate": 0.5, "latency_ms": 3000}
      }'
AgentOS will store the agent and return an agent_id.

5. Invoke through AgentOS
curl -X POST http://localhost:8080/v1/agents/<agent_id>/invoke \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
        "input_data": {
          "prompt": "Plan a low-carb dinner"
        },
        "timeout": 30
      }'
AgentOS proxies to your local FastAPI service, logs the metadata, and returns the result.

6. View it in the UI
Open http://localhost:3001:

Dashboard shows the new agent, invocations, denied counts, and policy alerts.
Logs & Trace Viewer display the trace emitted by the wrapper (telemetry_quality = “verified”).
Audit export contains each invocation with actor info if you need compliance logs.
Why you can’t point directly at Streamlit
Streamlit’s endpoint serves HTML/WebSocket traffic, not the JSON POST AgentOS expects, so you need the thin REST wrapper. Once it’s running, you can keep both: Streamlit for human interaction, and the FastAPI wrapper for AgentOS automation.

Feel free to adapt model_b_sample.py to call your exact agent (import the same tools/functions and reuse them inside /invoke). As long as you return a JSON payload like the sample does, AgentOS will “see” your agent just like any other Model B integration.

