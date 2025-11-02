



python model_b_sample.py






curl -X POST "http://localhost:8082/v1/agents/2afa8cf4-fd79-4204-9669-ab0bababfe68/invoke" \
  -H "Authorization: Bearer eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Ijp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA" \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"prompt": "Quick healthy snack"}}'





  User Request
    ↓
AgentOS Runtime (receives request)
    ↓
Logs: "Invocation started" ✅
    ↓
HTTP Proxy to YOUR service (model_b_sample.py on port 9001)
    ↓
YOUR CODE executes (on your machine)
    ↓
Response with telemetry ←
    ↓
AgentOS Runtime (receives response)
    ↓
Logs: "Invocation completed" ✅
    ↓
Stores in database ✅
    ↓
Shows in UI ✅


How It Works
Model B only requires:

✅ HTTP endpoint that accepts JSON
✅ Returns structured response (result + optional telemetry)
That's it! Doesn't matter where the agent runs.

Integration Examples
GCP Agent Space
bash
curl -X POST "http://localhost:8082/v1/agents/modelB" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gcp-agent",
    "description": "Agent running on GCP Agent Space",
    "endpoint_url": "https://your-project.run.app/invoke",
    "auth_config": {
      "type": "bearer",
      "token": "gcp-service-account-token"
    }
  }'
Salesforce Agentforce
bash
curl -X POST "http://localhost:8082/v1/agents/modelB" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "salesforce-agent",
    "description": "Agentforce agent",
    "endpoint_url": "https://yourorg.salesforce.com/services/agent/invoke",
    "auth_config": {
      "type": "bearer",
      "token": "salesforce-oauth-token"
    }
  }'
Microsoft Copilot / Azure
bash
curl -X POST "http://localhost:8082/v1/agents/modelB" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "copilot-agent",
    "description": "Azure-hosted Copilot agent",
    "endpoint_url": "https://your-app.azurewebsites.net/api/agent",
    "auth_config": {
      "type": "bearer",
      "token": "azure-ad-token"
    }
  }'
Any Custom Platform
bash
curl -X POST "http://localhost:8082/v1/agents/modelB" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom-agent",
    "endpoint_url": "https://anywhere.com/agent",
    "auth_config": {"type": "api_key", "header": "X-API-Key", "value": "key"}
  }'
Requirements for External Platforms
The external agent just needs to:

1. Accept HTTP POST
json
POST /invoke
{
  "input_data": { "prompt": "..." }
}
2. Return JSON Response
json
{
  "result": { "response": "..." },
  "telemetry": {  // Optional but recommended
    "trace": {
      "trace_id": "...",
      "execution_time_ms": 123
    }
  },
  "cost": 0.001  // Optional
}
What AgentOS Provides
Once registered, ALL external agents get:

✅ Unified API - Single endpoint for all agents
✅ Authentication - JWT-based access control
✅ Observability - Centralized logging & monitoring
✅ Policy Engine - Rate limiting, access control
✅ Cost Tracking - Aggregate costs across platforms
✅ UI Dashboard - View all agents in one place
✅ Telemetry - ATP v0 standard traces

Architecture
┌─────────────────────────────────────────────┐
│           AgentOS (Unified Layer)           │
│  - Single API endpoint                       │
│  - Authentication & Policy                   │
│  - Observability & Logging                   │
│  - Cost tracking                             │
└─────────────────────────────────────────────┘
              ↓ (Model B proxies)
    ┌─────────┬──────────┬──────────┬─────────┐
    ↓         ↓          ↓          ↓         ↓
┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌────────┐
│  GCP   │ │Salesf. │ │ Azure   │ │ Your   │ │ Model  │
│Agent   │ │Agent   │ │ Copilot │ │ Cloud  │ │  A     │
│Space   │ │force   │ │         │ │        │ │(local) │
└────────┘ └────────┘ └─────────┘ └────────┘ └────────┘
Example: Multi-Platform Setup
bash
# Register GCP agent
curl -X POST "$RUNTIME/v1/agents/modelB" -d '{"name": "gcp-recommender", "endpoint_url": "https://gcp.../invoke"}'

# Register Salesforce agent  
curl -X POST "$RUNTIME/v1/agents/modelB" -d '{"name": "salesforce-classifier", "endpoint_url": "https://salesforce.../invoke"}'

# Register Azure agent
curl -X POST "$RUNTIME/v1/agents/modelB" -d '{"name": "azure-analyzer", "endpoint_url": "https://azure.../invoke"}'

# Now invoke ANY agent via AgentOS
curl -X POST "$RUNTIME/v1/agents/{agent_id}/invoke" -d '{"input_data": {...}}'

# View ALL agents in ONE dashboard
open http://localhost:3001/agents
Benefits
Platform Agnostic - Don't lock into one vendor
Unified Monitoring - See all agents together
Cost Visibility - Track spending across platforms
Policy Consistency - Same rules for all agents
Easy Migration - Switch platforms without changing API
Summary
AgentOS Model B = Universal Agent Adapter

Works with ANY platform that has HTTP endpoints
Provides unified observability layer
Your agents stay on their native platforms
AgentOS acts as orchestration + monitoring hub
This is the key value of AgentOS - it doesn't force you to move agents, it federates them