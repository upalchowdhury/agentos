# AgentOS Local Development Runbook

**Complete guide to running AgentOS locally - from zero to deployed agents in 10 minutes**

## Prerequisites

- **Docker** (with PostgreSQL container running)
- **Python 3.9+**
- **Make** (for convenient commands)
- **curl** or **httpie** (for testing)

## Quick Start (TL;DR)

```bash
# From agentos/ops directory
make migrate        # Setup database schema
make runtime/dev    # Start runtime service
# In another terminal:
make seed          # Create demo agents
make monitor       # Watch metrics
```

**API will be available at:** `http://localhost:8000`
**Docs available at:** `http://localhost:8000/docs`

---

## Step-by-Step Setup

### 1. Database Setup

**Verify PostgreSQL is running:**
```bash
docker ps | grep agentos-postgres
```

If not running:
```bash
docker run -d --name agentos-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agentos \
  -p 5432:5432 \
  postgres:14
```

**Run migrations:**
```bash
cd /Users/upalc/AgentOS/agentos/ops
make migrate
```

Expected output:
```
Running database migrations...
CREATE TABLE
CREATE TABLE
...
✓ Migrations complete
```

**Verify schema:**
```bash
make migrate/status
```

Should show tables: `agents`, `agent_versions`, `invocations`, `cost_snapshots`, `roles`, `permissions`, etc.

---

### 2. Start Runtime Service

**Install dependencies:**
```bash
make runtime/install
```

**Start service:**
```bash
make runtime/dev
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Application startup complete.
```

**Verify service is running:**
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "runtime-service",
  "version": "0.2.0",
  "timestamp": "2025-10-27T..."
}
```

**View interactive API docs:**
Open browser to `http://localhost:8000/docs`

---

### 3. Create Your First Agent (Model A - Code Upload)

**Method 1: Using curl**

```bash
# Step 1: Create agent and get upload URL
curl -X POST http://localhost:8000/v1/agents/modelA \
  -H "Authorization: Bearer test_user_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world-agent",
    "runtime": "python3.11",
    "requirements": [],
    "env": {},
    "resources": {
      "cpu": "500m",
      "mem": "512Mi"
    }
  }'

# Response will include:
# {
#   "agent_id": "550e8400-e29b-41d4-a716-446655440000",
#   "upload_url": "https://...",
#   "deployment_id": "...",
#   "expires_at": "..."
# }

# Step 2: Upload code artifact (in real setup, upload to signed URL)
# For now, the demo script does this automatically

# Step 3: Check build status
curl http://localhost:8000/v1/agents/{agent_id}/build \
  -H "Authorization: Bearer test_user_token"

# Step 4: Invoke agent
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -H "Authorization: Bearer test_user_token" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "message": "Hello, world!"
    }
  }'
```

**Method 2: Using demo script**

```bash
# The deploy script creates a complete meal planning agent
make seed/agents
```

---

### 4. Register External Agent (Model B - Registry)

```bash
# Register an external agent endpoint
curl -X POST http://localhost:8000/v1/agents/modelB \
  -H "Authorization: Bearer test_user_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai-assistant",
    "endpoint_url": "https://api.openai.com/v1/assistants",
    "auth": {
      "type": "bearer",
      "value": "sk-..."
    },
    "rate_limit": {
      "rps": 10,
      "burst": 20
    }
  }'

# Response:
# {
#   "agent_id": "...",
#   "name": "openai-assistant",
#   "model_type": "B",
#   "status": "RUNNING",
#   "endpoint_url": "https://api.openai.com/v1/assistants",
#   ...
# }

# Invoke external agent (proxied through your platform)
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -H "Authorization: Bearer test_user_token" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "message": "What is 2+2?"
    }
  }'
```

---

### 5. Monitor Your Agents

**Real-time monitoring dashboard:**
```bash
make monitor
```

Output shows:
- 📊 Active agents
- 📈 Invocation statistics
- ⚡ Performance metrics (P50, P95, P99)
- 💰 Cost tracking
- ⚠️ Error analysis

**Continuous monitoring:**
```bash
watch -n 5 'make monitor'
```

**View specific agent:**
```bash
curl http://localhost:8000/v1/agents/{agent_id}
```

**Get metrics:**
```bash
curl "http://localhost:8000/v1/agents/{agent_id}/metrics?range=1d"
```

**Get costs:**
```bash
curl "http://localhost:8000/v1/agents/{agent_id}/costs?period=monthly"
```

---

### 6. Test RBAC with OPA

**Start OPA server:**
```bash
make opa/run
```

**Test policy decision:**
```bash
make opa/query
```

**Custom query:**
```bash
curl -X POST http://localhost:8181/v1/data/agentos/authz \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "subject_type": "user",
      "subject": {
        "id": "user_123",
        "roles": ["agent:executor"]
      },
      "agent_id": "agent_456",
      "agent": {
        "owner_id": "user_123"
      }
    }
  }'

# Response:
# {
#   "result": {
#     "allow": true,
#     "obligations": {
#       "audit_log": true,
#       "rate_limit": {"rps": 1, "burst": 5}
#     }
#   }
# }
```

**Stop OPA:**
```bash
make opa/stop
```

---

### 7. Agent-to-Agent (A2A) Invocation

**Scenario:** Agent A calls Agent B

```bash
# Create Agent A
AGENT_A_ID=$(curl -s -X POST http://localhost:8000/v1/agents/modelA \
  -H "Authorization: Bearer test_user_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "agent-a",
    "runtime": "python3.11",
    "requirements": [],
    "env": {}
  }' | jq -r '.agent_id')

# Create Agent B
AGENT_B_ID=$(curl -s -X POST http://localhost:8000/v1/agents/modelA \
  -H "Authorization: Bearer test_user_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "agent-b",
    "runtime": "python3.11",
    "requirements": [],
    "env": {}
  }' | jq -r '.agent_id')

# Grant A2A permission in OPA data.json or database
# Then Agent A can invoke Agent B:

curl -X POST http://localhost:8000/v1/agents/$AGENT_B_ID/invoke \
  -H "Authorization: Bearer agent_token_for_A" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"task": "process_data"},
    "caller_agent_id": "'$AGENT_A_ID'"
  }'
```

---

## Common Tasks

### List All Agents

```bash
curl http://localhost:8000/v1/agents \
  -H "Authorization: Bearer test_user_token"
```

### Get Agent Details

```bash
curl http://localhost:8000/v1/agents/{agent_id} \
  -H "Authorization: Bearer test_user_token"
```

### Delete Agent

```bash
curl -X DELETE http://localhost:8000/v1/agents/{agent_id} \
  -H "Authorization: Bearer test_user_token"
```

### Query Database Directly

```bash
# View all agents
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT * FROM agents;"

# View invocations
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT * FROM invocations ORDER BY started_at DESC LIMIT 10;"

# View cost snapshots
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT * FROM cost_snapshots;"

# View A2A invocation graph
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT * FROM a2a_invocation_graph;"
```

### Run Security Audit

```bash
make security
```

Shows:
- 🔐 RBAC roles and permissions
- 🔑 Agent role assignments
- 🚫 Denied access attempts
- ⚠️ Content violations

---

## Troubleshooting

### Service Won't Start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process if needed
kill -9 $(lsof -t -i:8000)

# Check database connection
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT 1"
```

### Database Connection Errors

```bash
# Verify .env file exists
cat /Users/upalc/AgentOS/agentos/services/runtime/.env

# Should contain:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=agentos
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
```

### Build Failures

```bash
# Check build logs
curl http://localhost:8000/v1/agents/{agent_id}/build

# View service logs
tail -f /path/to/logs

# Or in k8s:
kubectl logs -f -l app=runtime-service
```

### OPA Policy Errors

```bash
# Test OPA policies
make opa/test

# Validate policy syntax
docker run --rm -v $(pwd)/../infra/opa:/policies \
  openpolicyagent/opa:latest \
  check /policies
```

---

## Development Workflow

### Making Changes

1. **Edit code** in `services/runtime/src/`
2. **Service auto-reloads** (watch for reload message in logs)
3. **Test changes** via curl or API docs
4. **Run tests:** `make test`

### Adding New Endpoints

1. Add route in `src/api/agents_v2.py`
2. Add model in `src/models_v2.py`
3. Update `openapi/api.yaml`
4. Add OPA policy if needed
5. Write tests
6. Run `make test`

### Database Changes

1. Create new migration file: `infra/migrations/006_your_change.sql`
2. Run migration: `make migrate`
3. Update models and queries

---

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test invocation endpoint
ab -n 1000 -c 10 -p payload.json -T application/json \
  -H "Authorization: Bearer test_token" \
  http://localhost:8000/v1/agents/{agent_id}/invoke
```

### Monitor Performance

```bash
# Watch metrics in real-time
watch -n 1 'curl -s http://localhost:8000/v1/agents/{agent_id}/metrics | jq .'
```

---

## Next Steps

1. **Explore API Docs:** `http://localhost:8000/docs`
2. **Read OpenAPI Spec:** `openapi/api.yaml`
3. **Review OPA Policies:** `infra/opa/*.rego`
4. **Run Tests:** `make test`
5. **Deploy to K8s:** `make kind-up && make runtime/deploy`

---

## Complete Example: LangChain Agent

```python
# agent_code.py
from langchain.agents import create_openai_agent
from langchain.llms import OpenAI
import os

# input_data provided by runtime
customer_message = input_data['message']

# Initialize agent
agent = create_openai_agent(
    llm=OpenAI(api_key=os.getenv('OPENAI_API_KEY')),
    tools=[],
    prompt="You are a helpful assistant"
)

# Execute
response = agent.run(customer_message)

# Return result (runtime expects this format)
result = {
    "response": response,
    "timestamp": "executed"
}
```

**Deploy this agent:**
```bash
# Create agent
curl -X POST http://localhost:8000/v1/agents/modelA \
  -H "Authorization: Bearer test_token" \
  -d '{
    "name": "langchain-support",
    "runtime": "python3.11",
    "requirements": ["langchain", "openai"],
    "env": {"OPENAI_API_KEY": "sk-..."}
  }'

# Upload code (upload to returned URL)
# Build happens automatically

# Invoke
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -d '{"input_data": {"message": "Hello"}}'
```

---

## Support

- **Logs:** Service logs show detailed execution traces
- **Database:** Query `invocations` table for full audit trail
- **Metrics:** Use monitoring dashboard for real-time metrics
- **Security:** Run `make security` for RBAC audit

**You're ready to build and deploy agents! 🚀**
