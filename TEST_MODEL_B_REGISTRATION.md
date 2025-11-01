# Model B Agent Registration - Testing Guide

## Status: ✅ Backend Fully Implemented

All Model B registration capabilities are now live in the AgentOS runtime service.

## Current Architecture

```
┌──────────┐     ┌─────────┐     ┌─────────┐     ┌──────────────┐
│  Web UI  │────▶│ Gateway │────▶│ Runtime │────▶│ PostgreSQL   │
│  :3001   │     │  :8080  │     │  :8082  │     │              │
└──────────┘     └─────────┘     └─────────┘     └──────────────┘
                      │
                      ▼
                 ┌──────────┐
                 │ Identity │
                 │  :3000   │
                 └──────────┘
```

## ✅ Working: Direct Runtime API

The runtime service (`http://localhost:8082`) has full Model B support:

### 1. Register External Agent

```bash
curl -X POST http://localhost:8082/v1/agents/modelB \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-external-agent",
    "endpoint_url": "http://localhost:9000/invoke",
    "auth": {"type": "none"},
    "rate_limit": {"rps": 10, "burst": 20},
    "health_check_path": "/health",
    "timeout_seconds": 30,
    "alerts": {
      "error_rate": 0.4,
      "latency_ms": 2500
    }
  }'
```

**Response:**
```json
{
  "agent_id": "95c9e368-ebbe-406b-aaa6-7a1367e14830",
  "name": "my-external-agent",
  "owner_id": "user_test-tok",
  "model_type": "B",
  "status": "RUNNING",
  "telemetry_quality": "partial",
  "endpoint_url": "http://localhost:9000/invoke",
  "health_status": "healthy",
  "created_at": "2025-11-01T02:08:06.530947",
  "deployed_at": "2025-11-01T02:08:06.530947",
  "invocation_count": 0,
  "cost_to_date": 0.0
}
```

### 2. List Agents

```bash
curl http://localhost:8082/v1/agents \
  -H "Authorization: Bearer test-token"
```

### 3. Get Observability Data

```bash
# Agent telemetry
curl "http://localhost:8082/v1/observability/agents?range=1d" \
  -H "Authorization: Bearer test-token"

# Recent invocations
curl "http://localhost:8082/v1/observability/agents/invocations?limit=20" \
  -H "Authorization: Bearer test-token"

# Logs
curl "http://localhost:8082/v1/observability/logs?limit=100" \
  -H "Authorization: Bearer test-token"

# Audit export
curl "http://localhost:8082/v1/observability/audit/export" \
  -H "Authorization: Bearer test-token" \
  --output audit_export.csv
```

## 🔧 Gateway Authentication (Known Issue)

The gateway at `:8080` requires valid JWT tokens from the identity service. Currently experiencing signature verification issues.

**Workaround:** Access runtime service directly at `http://localhost:8082` for testing.

## 🎨 Web UI

The Web UI has full support for Model B registration:

1. **Navigate to:** http://localhost:3001/register-external
2. **Fill in the form:**
   - Agent Name
   - Endpoint URL
   - Authentication type (None/Bearer/Header)
   - Rate limits (RPS/Burst)
   - Health check path
   - Optional alert thresholds

3. **Agent listing:** http://localhost:3001/agents
   - Shows all registered agents
   - Displays Model A vs Model B
   - Shows telemetry quality badges

4. **Dashboard:** http://localhost:3001
   - Export Audit button for CSV download
   - Agent telemetry summaries
   - Policy alerts

## 📊 Database Schema

The `agents` table supports both Model A and Model B:

```sql
SELECT id, name, model_type, status, endpoint_url, health_status 
FROM agents 
WHERE model_type = 'B';
```

## 🚀 Next Steps

1. **Fix Gateway Auth:** Resolve JWT verification between gateway and identity service
2. **Test A2A Invocation:** Agent-to-agent calls with caller_agent_id
3. **Policy Integration:** OPA-based policy enforcement
4. **SDK Integration:** Test verified telemetry upgrade with Python SDK

## 📝 Implementation Checklist

- ✅ Runtime service with Model B registration endpoint
- ✅ External agent proxy with health checks
- ✅ Rate limiting enforcement
- ✅ Alert threshold configuration
- ✅ Database schema with agents table
- ✅ Observability endpoints (agents, invocations, logs, audit)
- ✅ Web UI registration form
- ✅ Web UI agents listing page
- ✅ Web UI dashboard with export
- ✅ Gateway routing to runtime service
- ⚠️  Gateway JWT authentication (needs fix)
- ⏳ End-to-end agent invocation flow
- ⏳ Telemetry upgrade (partial → verified)
