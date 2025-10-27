# Complete Guide: Deploy & Monitor Agent with RBAC/Logging/Security

**Quick 5-Step Process to deploy an agent and monitor everything**

## Setup (One-Time)

### 1. Load All Database Schemas

```bash
cd /Users/upalc/AgentOS/agentos

# Load all required schemas
docker exec -i agentos-postgres psql -U postgres -d agentos < infra/migrations/001_initial_schema.sql
docker exec -i agentos-postgres psql -U postgres -d agentos < infra/migrations/003_rbac_schema.sql
docker exec -i agentos-postgres psql -U postgres -d agentos < infra/migrations/004_runtime_schema.sql

# Verify tables exist
docker exec agentos-postgres psql -U postgres -d agentos -c "\dt"
```

Expected output:
```
 agent_deployments
 agent_invocations
 agent_metrics
 agent_roles
 permissions
 roles
 content_violations
```

### 2. Configure Runtime Service

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime

# Create environment configuration (skip if exists)
cat > .env << 'EOF'
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DEBUG=true
HOST=0.0.0.0
PORT=8000
EOF
```

## Deployment Workflow

### Terminal 1: Start Runtime Service

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python -m src.main
```

**Expected Logs:**
```
2024-10-26 22:00:00 - src.main - INFO - Starting Runtime service
2024-10-26 22:00:00 - src.database - INFO - Connecting to database...
2024-10-26 22:00:00 - src.main - INFO - Runtime service ready
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Deploy Agent with Monitoring

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python deploy_monitored_agent.py
```

**What This Does:**
1. ✅ Deploys a meal planning agent to AgentOS
2. ✅ Tests it with 3 different meal requests
3. ✅ Verifies deployment status
4. ✅ Shows performance metrics

**Expected Output:**
```
==================================================================================
DEPLOYING AGENT WITH SECURITY & LOGGING MONITORING
==================================================================================
Timestamp: 2024-10-26T22:00:00.123456
Agent ID: meal-planner-agent-v1
Memory Limit: 256m
CPU Limit: 0.25

[STEP 1] DEPLOYING AGENT...
----------------------------------------------------------------------------------
✅ Deployment successful!
   Deployment ID: 550e8400-e29b-41d4-a716-446655440000
   Status: RUNNING
   Deployed At: 2024-10-26T22:00:00.123456

[STEP 2] TESTING AGENT INVOCATIONS...
----------------------------------------------------------------------------------
   Test 1/3: {'meal_type': 'breakfast', 'dietary': 'balanced', 'servings': 2}
   ✅ Status: SUCCESS
      Output: {
         "meal_type": "breakfast",
         "recommendation": "Oatmeal with berries and nuts",
         "nutrition": {
            "calories_per_serving": 320,
            "protein_grams": 12,
            "total_calories": 640
         }
      }
      Execution Time: 15ms
      Cost: $0.01
...
```

### Terminal 3: Monitor in Real-Time

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python monitor_agent.py
```

**What This Shows:**
- 📊 Active agents and their status
- 📈 Invocation statistics (success rate, timing)
- ⚠️ Error analysis
- ⚡ Performance metrics (P50, P95, P99)
- 💰 Cost analysis
- 🔒 Security audit logs
- 📊 Aggregated statistics

**Sample Output:**
```
==================================================================================
AGENTOS MONITORING DASHBOARD - 2024-10-26 22:05:00
==================================================================================

📊 ACTIVE AGENTS
----------------------------------------------------------------------------------
   • Agent: meal-planner-agent-v1
     Status: RUNNING | Deployed: 2024-10-26 22:00:00 | Memory: 256m | CPU: 0.25

📈 INVOCATIONS (Last 1 Hour)
----------------------------------------------------------------------------------
   • Agent: meal-planner-agent-v1
     Invocations: 3 | Success: 3 (100.0%) | Errors: 0 | Timeouts: 0
     Avg Time: 14.33ms | Total Cost: $0.0003

⚡ PERFORMANCE METRICS
----------------------------------------------------------------------------------
   • Agent: meal-planner-agent-v1
     Samples: 3 | Avg: 14.33ms | P50: 14ms | P95: 15ms | P99: 15ms
     Min: 13ms | Max: 16ms
```

## Security Monitoring

### Check RBAC & Security Logs

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
./check_security.sh
```

**What This Shows:**
- 🔐 All RBAC roles and permissions
- 🔑 Agent role assignments
- 📋 Recent access attempts
- 🚫 Denied access (security violations)
- ⚠️ Content policy violations
- 💡 Agents without roles (security risk)

### Manual Security Queries

```bash
# View all roles and their permissions
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT r.name, r.description, COUNT(p.id) as permissions
FROM roles r
LEFT JOIN permissions p ON r.name = p.role_name
GROUP BY r.name, r.description;
"

# Assign role to your agent
docker exec agentos-postgres psql -U postgres -d agentos -c "
INSERT INTO agent_roles (agent_did, role_name, granted_by)
VALUES ('meal-planner-agent-v1', 'agent:executor', 'admin')
ON CONFLICT DO NOTHING;
"

# View agent permissions
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT ar.agent_did, ar.role_name, p.resource, p.action
FROM agent_roles ar
JOIN permissions p ON ar.role_name = p.role_name
WHERE ar.agent_did = 'meal-planner-agent-v1';
"
```

## Real-Time Monitoring Commands

### Watch Server Logs (Terminal 1)

While runtime service is running, you'll see:

**Deployment:**
```
INFO - Deployed agent meal-planner-agent-v1 with deployment_id 550e8400-e29b-41d4-a716-446655440000
```

**Invocation:**
```
INFO - Invoked agent meal-planner-agent-v1, invocation_id abc123, status SUCCESS
```

**Errors:**
```
ERROR - Agent meal-planner-agent-v1 execution error: division by zero
```

### Query Database Directly

```bash
# View all deployments
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT agent_did, status, deployed_at FROM agent_deployments;
"

# View invocation history
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT agent_did, status, execution_time_ms, cost_cents, invoked_at 
FROM agent_invocations 
ORDER BY invoked_at DESC 
LIMIT 10;
"

# View aggregated stats
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT * FROM agent_stats WHERE agent_did = 'meal-planner-agent-v1';
"

# Check error rate
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    agent_did,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'ERROR') / COUNT(*), 2) as error_rate_pct
FROM agent_invocations
GROUP BY agent_did;
"
```

## Continuous Monitoring Loop

For continuous real-time monitoring:

```bash
# Monitor every 5 seconds
watch -n 5 'python monitor_agent.py'

# Or create a loop
while true; do 
    clear
    python monitor_agent.py
    sleep 5
done
```

## Production Enhancements

### 1. Structured JSON Logging

Add to `services/runtime/src/config.py`:

```python
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "runtime-service"
        })

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

### 2. Export Logs to File

```bash
# In Terminal 1 (when starting service)
python -m src.main 2>&1 | tee logs/runtime-$(date +%Y%m%d-%H%M%S).log
```

### 3. Integrate with Observability Stack

```bash
# Send logs to ClickHouse or Elasticsearch
# Configure OpenTelemetry for traces
# Set up Prometheus for metrics
# Create Grafana dashboards
```

## Complete Test Flow

**One-command full test:**

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime

# Terminal 1
python -m src.main &

# Wait for startup
sleep 3

# Terminal 2 - Deploy and test
python deploy_monitored_agent.py

# Terminal 3 - Monitor
python monitor_agent.py

# Terminal 4 - Security check
./check_security.sh
```

## Troubleshooting

### Runtime service won't start

```bash
# Check database connection
docker exec agentos-postgres psql -U postgres -d agentos -c "SELECT 1"

# Check if port is in use
lsof -i :8000

# Check environment
cat services/runtime/.env
```

### Agent deployment fails

```bash
# Check server logs in Terminal 1
# Verify schema exists
docker exec agentos-postgres psql -U postgres -d agentos -c "\dt agent_*"

# Test API directly
curl http://localhost:8000/
```

### Monitoring shows no data

```bash
# Check if agent was deployed
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT * FROM agent_deployments;
"

# Check if invocations were recorded
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT COUNT(*) FROM agent_invocations;
"
```

## Summary

You now have a complete deployment and monitoring system:

✅ **Deployed agent** - meal-planner-agent-v1 running in AgentOS
✅ **Logging** - All operations logged with timestamps and context
✅ **RBAC** - Role-based access control configured
✅ **Security** - Audit logs for all access attempts
✅ **Monitoring** - Real-time dashboard with metrics
✅ **Database** - All data persisted and queryable

**Key Files:**
- `services/runtime/deploy_monitored_agent.py` - Deploy script
- `services/runtime/monitor_agent.py` - Monitoring dashboard
- `services/runtime/check_security.sh` - Security audit
- `services/runtime/src/api/agents.py` - API with logging
- `infra/migrations/003_rbac_schema.sql` - RBAC schema
- `infra/migrations/004_runtime_schema.sql` - Runtime schema

**Next Steps:**
1. Create custom agents for your use case
2. Set up automated monitoring alerts
3. Integrate with OpenTelemetry/Grafana
4. Add authentication middleware
5. Deploy to production environment
