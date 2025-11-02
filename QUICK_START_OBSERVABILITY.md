# AgentOS Observability - Quick Start Guide

Get the complete observability stack running in 5 minutes.

---

## Prerequisites

- Python 3.11+
- Go 1.21+
- PostgreSQL 16
- Docker (optional, for OTel/Jaeger)

---

## Step 1: Database Setup (1 min)

```bash
# Start PostgreSQL
docker run -d --name agentos-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agentos \
  -p 5432:5432 postgres:16

# Wait for startup
sleep 5

# Apply schema
cd /Users/upalc/AgentOS/agentos/infra/migrations
psql -h localhost -U postgres -d agentos < 005_enhanced_runtime_schema.sql
```

---

## Step 2: Start Services (2 min)

Open 5 terminal windows:

### Terminal 1: Runtime Service
```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python -m src.main
```
**Listens on:** http://localhost:8000

### Terminal 2: ATP Ingest
```bash
cd /Users/upalc/AgentOS/agentos/services/observability/ingest
pip install -r requirements.txt
python main.py
```
**Listens on:** http://localhost:8001

### Terminal 3: OTel Bridge
```bash
cd /Users/upalc/AgentOS/agentos/services/observability/o11y-bridge
pip install -r requirements.txt
python main.py
```
**Listens on:** http://localhost:8002

### Terminal 4: Observability API
```bash
cd /Users/upalc/AgentOS/agentos/services/observability/api
pip install -r requirements.txt
python main.py
```
**Listens on:** http://localhost:8003

### Terminal 5: Gateway (Optional)
```bash
cd /Users/upalc/AgentOS/agentos/services/gateway
go run cmd/server/main.go
```
**Listens on:** http://localhost:8080

---

## Step 3: Verify Health (30 sec)

```bash
# Check all services
curl http://localhost:8000/health  # Runtime
curl http://localhost:8001/health  # Ingest
curl http://localhost:8002/health  # Bridge
curl http://localhost:8003/health  # Observability
curl http://localhost:8080/health  # Gateway (if running)
```

All should return `{"status":"healthy"}`

---

## Step 4: Create & Invoke Agent (1 min)

```bash
# Create Model A agent
curl -X POST http://localhost:8000/v1/agents/modelA \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-agent",
    "runtime": "python3.11",
    "code": "def handle(input): return {\"message\": \"Hello from agent!\"}",
    "requirements": []
  }'

# Save the agent_id from response
AGENT_ID="<your-agent-id>"

# Invoke agent
curl -X POST http://localhost:8000/v1/agents/$AGENT_ID/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "World"}}'

# Save the trace_id from response
TRACE_ID="<your-trace-id>"
```

---

## Step 5: View Observability (30 sec)

```bash
# Get full trace with steps
curl http://localhost:8003/v1/traces/$TRACE_ID | jq

# Get agent metrics
curl http://localhost:8003/v1/agents/$AGENT_ID/metrics | jq

# Get cost summary
curl http://localhost:8000/v1/cost/summary?agent_id=$AGENT_ID | jq

# Browse catalog
curl http://localhost:8000/v1/catalog/agents | jq
```

---

## Step 6: Test ATP Ingest (30 sec)

```bash
# Send telemetry event
curl -X POST http://localhost:8001/v1/telemetry/events \
  -H "Content-Type: application/json" \
  -d '{
    "trace": {
      "trace_id": "test-trace-123",
      "invocation_id": "test-inv-123",
      "agent_id": "'$AGENT_ID'",
      "status": "success",
      "start_ts": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "end_ts": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "execution_time_ms": 250,
      "cost_cents": 5
    },
    "steps": [
      {
        "step_id": "step-1",
        "name": "process",
        "kind": "tool",
        "start_ts": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "end_ts": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "latency_ms": 200,
        "status": "success"
      }
    ]
  }'

# Verify trace is accessible
sleep 2
curl http://localhost:8003/v1/traces/test-trace-123 | jq
```

---

## Optional: OTel Stack

### Start Jaeger
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one
```

View traces: http://localhost:16686

### Start OTel Collector
```bash
docker run -d --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  otel/opentelemetry-collector
```

---

## Test Scenarios

### Scenario 1: Cost Tracking
```bash
# Get top spending agents
curl http://localhost:8000/v1/cost/top-spending?limit=5 | jq

# Check budget
curl "http://localhost:8000/v1/cost/agents/$AGENT_ID/budget?budget_limit_usd=10&period=daily" | jq
```

### Scenario 2: Replay
```bash
# Get invocation ID from earlier invoke
INVOCATION_ID="<from-invoke-response>"

# Prepare replay
curl -X POST http://localhost:8000/v1/replay/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "invocation_id": "'$INVOCATION_ID'",
    "replay_mode": "strict"
  }' | jq

# Execute replay
curl -X POST http://localhost:8000/v1/replay/execute \
  -H "Content-Type: application/json" \
  -d '{
    "invocation_id": "'$INVOCATION_ID'",
    "replay_mode": "strict"
  }' | jq
```

### Scenario 3: Catalog with Badges
```bash
# Browse catalog with filters
curl "http://localhost:8000/v1/catalog/agents?sort_by=popularity&limit=10" | jq

# Get catalog stats
curl http://localhost:8000/v1/catalog/stats | jq

# Get filter options
curl http://localhost:8000/v1/catalog/filters | jq
```

### Scenario 4: Obligations (Redaction)
```bash
# Test redaction in Python
python3 << 'EOF'
import sys
sys.path.append('/Users/upalc/AgentOS/agentos/services/runtime')

from src.obligations import obligations_engine

# Test data with PII
data = {
    "message": "My SSN is 123-45-6789 and credit card is 4532-1234-5678-9010",
    "email": "user@example.com"
}

# Apply redaction
redacted, rules = obligations_engine.redact_dict(data)

print("Original:", data)
print("Redacted:", redacted)
print("Applied rules:", rules)
EOF
```

---

## Run Integration Tests

```bash
cd /Users/upalc/AgentOS/agentos
pytest tests/integration/test_e2e_scenarios.py -v
```

---

## API Documentation

Once services are running, visit:

- Runtime API Docs: http://localhost:8000/docs
- Ingest API Docs: http://localhost:8001/docs
- Bridge API Docs: http://localhost:8002/docs
- Observability API Docs: http://localhost:8003/docs
- Gateway Root: http://localhost:8080/

---

## Troubleshooting

### Service won't start
```bash
# Check port availability
lsof -i :8000  # Replace with actual port

# Check dependencies
pip install -r requirements.txt
```

### Database connection error
```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U postgres -d agentos -c "SELECT 1"

# Check credentials in code
# Default: localhost:5432, user=postgres, password=postgres, db=agentos
```

### No traces appearing
```bash
# Check ingest service logs
# Verify database has invocations
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT COUNT(*) FROM invocations"

# Check trace ID matches
curl http://localhost:8003/v1/traces | jq
```

---

## Production Deployment

See `OBSERVABILITY_IMPLEMENTATION_COMPLETE.md` for:
- Kubernetes deployment manifests
- Envoy sidecar configuration
- Environment variable setup
- Security hardening
- Performance tuning

---

## Next Steps

1. ✅ Configure Slack webhook for alerts
2. ✅ Set up Grafana dashboards via OTel
3. ✅ Deploy Envoy sidecar to production agents
4. ✅ Configure budget caps for cost control
5. ✅ Enable protocol policy packs (A2A/MCP)

---

**You're ready to observe!** 🚀

All services running? Test an invoke and watch the telemetry flow through the entire stack.
