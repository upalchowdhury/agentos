# Deploy AgentOS to Kubernetes (Docker Desktop)

Complete guide to deploy and test the observability stack.

---

## Prerequisites

1. **Docker Desktop** with Kubernetes enabled
   - Open Docker Desktop → Settings → Kubernetes → Enable Kubernetes
   - Wait for cluster to start (green indicator)

2. **kubectl** installed
   ```bash
   kubectl version --client
   ```

3. **Python 3.11+** for test agent
   ```bash
   python3 --version
   ```

---

## Quick Deploy (5 minutes)

```bash
cd /Users/upalc/AgentOS/agentos

# Make scripts executable
chmod +x deploy-k8s.sh test-model-b.sh

# Deploy entire stack
./deploy-k8s.sh
```

This will:
- Create `agentos` namespace
- Deploy PostgreSQL with persistent storage
- Deploy Runtime, Ingest, OTel Bridge, Observability API
- Initialize database schema
- Wait for all services to be ready
- Run health checks

---

## Service Endpoints

Once deployed, services are available at:

| Service | URL | Docs |
|---------|-----|------|
| Runtime API | http://localhost:30000 | http://localhost:30000/docs |
| ATP Ingest | http://localhost:30001 | http://localhost:30001/docs |
| Observability API | http://localhost:30003 | http://localhost:30003/docs |

---

## Test Model B Agent

### Step 1: Install Dependencies

```bash
pip install fastapi uvicorn httpx pydantic
```

### Step 2: Start Test Agent

```bash
# Terminal 1: Start the test agent
cd testAgents
python model_b_agent.py
```

Agent will run on http://localhost:9000

### Step 3: Register Agent

```bash
# Terminal 2: Register with AgentOS
./test-model-b.sh register
```

**Expected output:**
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "model-b-test-agent",
  "status": "registered",
  "model_type": "B"
}
```

**Save the `agent_id`!**

### Step 4: Invoke Agent

```bash
export AGENT_ID="<your-agent-id-from-step-3>"

./test-model-b.sh invoke $AGENT_ID
```

**Expected output:**
```json
{
  "output": {
    "result": "success",
    "message": "Processed: {...}",
    "timestamp": "2025-11-02T18:44:00.000000"
  },
  "trace_id": "abc123...",
  "invocation_id": "def456...",
  "execution_time_ms": 205
}
```

### Step 5: View Telemetry

```bash
# View trace with steps
./test-model-b.sh view-trace <trace-id>

# View agent metrics
./test-model-b.sh agent-metrics $AGENT_ID

# View all traces
./test-model-b.sh list-traces

# View cost summary
./test-model-b.sh cost-summary

# Browse catalog
./test-model-b.sh catalog
```

---

## Verify Complete Flow

### 1. Check All Services Healthy
```bash
./test-model-b.sh health
```

All should return `{"status": "healthy"}`

### 2. View Kubernetes Resources
```bash
kubectl get all -n agentos
```

Should show:
- 1 PostgreSQL pod (running)
- 2 Runtime pods (running)
- 2 Ingest pods (running)
- 1 OTel Bridge pod (running)
- 2 Observability API pods (running)

### 3. Check Logs
```bash
# Runtime service
kubectl logs -f -l app=runtime -n agentos

# Ingest service (see telemetry arriving)
kubectl logs -f -l app=ingest -n agentos

# Observability API
kubectl logs -f -l app=observability-api -n agentos
```

### 4. Direct API Tests

```bash
# Create and invoke flow
curl http://localhost:30000/health

# Send telemetry directly
curl -X POST http://localhost:30001/v1/telemetry/events \
  -H "Content-Type: application/json" \
  -d '{
    "trace": {
      "trace_id": "manual-test-123",
      "invocation_id": "manual-inv-123",
      "agent_id": "test-agent",
      "protocol": "http",
      "status": "success",
      "start_ts": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "end_ts": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "execution_time_ms": 100,
      "cost_cents": 5
    },
    "steps": []
  }'

# Retrieve trace
curl http://localhost:30003/v1/traces/manual-test-123 | jq
```

---

## Test Scenarios

### Scenario 1: Complete Model B Flow ✅
```bash
# 1. Register agent
./test-model-b.sh register
# Output: agent_id

# 2. Invoke 10 times
for i in {1..10}; do
  ./test-model-b.sh invoke $AGENT_ID
  sleep 1
done

# 3. View metrics
./test-model-b.sh agent-metrics $AGENT_ID

# Should show:
# - total_invocations: 10
# - success_rate_pct: 100.0
# - avg_latency_ms: ~200
```

### Scenario 2: Catalog with Badges ✅
```bash
# View catalog
./test-model-b.sh catalog

# Look for badges:
# - "verified_telemetry" (after ATP events sent)
# - "cost_tagged" (if cost data present)
```

### Scenario 3: Cost Tracking ✅
```bash
# Get summary
curl "http://localhost:30000/v1/cost/summary?agent_id=$AGENT_ID&period_days=1" | jq

# Should show:
# - invocation_count
# - total_cost_usd
# - avg_cost_per_invocation_usd
```

### Scenario 4: Trace Explorer ✅
```bash
# List all traces
curl "http://localhost:30003/v1/traces?agent_id=$AGENT_ID&limit=5" | jq

# Get specific trace with steps
curl "http://localhost:30003/v1/traces/<trace-id>" | jq

# Verify steps array has data
```

---

## Troubleshooting

### Services won't start
```bash
# Check pod status
kubectl get pods -n agentos

# View pod details
kubectl describe pod <pod-name> -n agentos

# Check logs
kubectl logs <pod-name> -n agentos
```

### Database connection issues
```bash
# Verify PostgreSQL is running
kubectl get pod -l app=postgres -n agentos

# Check database logs
kubectl logs -l app=postgres -n agentos

# Verify init job completed
kubectl get job init-db -n agentos
kubectl logs job/init-db -n agentos
```

### Test agent can't connect
```bash
# Verify NodePort services
kubectl get svc -n agentos

# Test from inside cluster
kubectl run -it --rm debug --image=alpine --restart=Never -n agentos -- sh
# Inside pod:
apk add curl
curl http://runtime:8000/health
```

### Telemetry not appearing
```bash
# Check ingest service logs
kubectl logs -f -l app=ingest -n agentos

# Verify database has data
kubectl exec -it postgres-0 -n agentos -- psql -U postgres -d agentos -c "SELECT COUNT(*) FROM invocations"

# Check test agent is sending
# In test agent logs, should see: "Telemetry sent successfully"
```

---

## Load Testing

```bash
# Install hey (HTTP load testing tool)
go install github.com/rakyll/hey@latest

# Load test invocation
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"input":{"test":"data"}}' \
  http://localhost:9000/invoke

# Should handle 100 requests successfully
```

---

## Clean Up

```bash
# Delete entire deployment
kubectl delete namespace agentos

# Or delete specific resources
kubectl delete -f infra/k8s/observability-stack.yaml
kubectl delete -f infra/k8s/init-db-job.yaml

# Verify cleanup
kubectl get all -n agentos
```

---

## Production Considerations

Before production deployment:

1. **Resource Limits** - Adjust CPU/memory based on load
2. **Persistent Storage** - Use proper PV provisioner (not hostPath)
3. **Secrets Management** - Use Kubernetes Secrets or external vault
4. **Ingress** - Set up proper Ingress controller instead of NodePort
5. **Monitoring** - Deploy Prometheus/Grafana for metrics
6. **Logging** - Use centralized logging (ELK/Loki)
7. **Backups** - Configure PostgreSQL backups
8. **TLS** - Enable HTTPS for all services
9. **Horizontal Scaling** - Configure HPA for auto-scaling
10. **Network Policies** - Restrict inter-service communication

---

## Success Criteria

Your deployment is successful when:

- ✅ All pods are `Running` and `Ready`
- ✅ All services return `{"status": "healthy"}`
- ✅ Model B agent can be registered
- ✅ Invocations complete successfully
- ✅ Telemetry appears in traces API within 5 seconds
- ✅ Metrics show accurate counts
- ✅ Cost tracking displays data
- ✅ Catalog shows agent with badges

---

## Next Steps

1. ✅ Deploy to production Kubernetes cluster
2. ✅ Set up monitoring dashboards
3. ✅ Configure alerts (Slack/Email)
4. ✅ Enable A2A policy packs
5. ✅ Deploy more Model B agents
6. ✅ Integrate with existing infrastructure

---

**🎉 You now have a production-grade observability stack running in Kubernetes!**
