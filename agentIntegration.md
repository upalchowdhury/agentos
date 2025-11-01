To wire an AI agent that’s already running on your laptop into AgentOS, you simply treat it as a Model B “external” agent. Here’s the full loop:

1. Make sure your agent exposes an HTTP endpoint
AgentOS calls your agent via HTTP POST. Your service should accept JSON like:

{ "input_data": { ... } }
…and return a JSON payload, optionally including telemetry:

{
  "result": { "answer": 42 },
  "metadata": {
    "telemetry": {
      "trace": { ... }   // optional; see SDK notes below
    }
  },
  "cost": 0.0
}
If you want “Verified Telemetry” later, emit detailed traces via the SDK; otherwise the proxy will show “Partial Telemetry”.

2. Register the agent with AgentOS (Model B)
Spin up the local stack (make dev-up) if it’s not already running.
Then register your external endpoint:

curl -X POST http://localhost:8080/v1/agents/modelB \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "local-reasoner",
        "endpoint_url": "http://localhost:9000/invoke",   // your agent’s URL
        "auth": {"type": "none"},
        "rate_limit": {"rps": 5, "burst": 10},
        "health_check_path": "/health",
        "alerts": { "error_rate": 0.4, "latency_ms": 2500 }
      }'
You’ll get back an agent_id—you’ll use it for invocations.

You can also do this inside the UI: go to Agents → Register Agent, fill in the same fields, and click save.

3. Invoke the agent through AgentOS
curl -X POST http://localhost:8080/v1/agents/<agent_id>/invoke \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
        "input_data": {
          "question": "How do I debug partial telemetry?"
        },
        "timeout": 30
      }'
AgentOS will proxy to your local service, store metadata, and return status/cost.

4. Observe everything in the UI
Dashboard (http://localhost:3001) shows the agent’s invocations, denied counts, and policy alerts.
Logs page lets you filter by agent, level, subject type, trace ID.
Trace Viewer provides step/log drilldown; “Partial Telemetry” badge appears until you emit SDK traces.
Audit Export stream (Dashboard → Audit → Export) gives you CSV history with actor/policy context.
5. (Optional) Upgrade to verified telemetry
If you want the “Verified” badge and step-level traces, instrument your agent with the AgentOS telemetry SDK so it posts telemetry.trace payloads back to the runtime. Drop the lightweight client into your agent code:

from agentos_sdk import TelemetryClient

telemetry = TelemetryClient(agent_id="<agent_id>", base_url="http://localhost:8080")
with telemetry.trace("step-name") as span:
    ...  # run your agent logic
    span.log("info", "Built plan")
After the first SDK trace arrives, the runtime updates the agent record to “verified” and the UI gets richer traces.

That’s it—AgentOS now treats your locally running AI service exactly like any other Model B agent, with rate limiting, alert thresholds, observability dashboards, and audit trails.