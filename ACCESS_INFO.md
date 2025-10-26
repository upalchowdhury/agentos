# 🚀 Agent Economy OS - Access Information

## Your Application is Running!

All services are deployed in Kubernetes and accessible via port forwarding.

### 🌐 Web Dashboard
**URL:** http://localhost:3001

**Features:**
- Real-time dashboard with live metrics
- Agent registry and management
- Register new agents with custom metadata
- View role assignments and credentials

**Pages:**
- **Dashboard** - View metrics, recent agents, role distribution
- **Agent Registry** - Browse all registered agents
- **Register Agent** - Create new agent DIDs

---

### 🔌 API Endpoints

#### Identity Service API
**Base URL:** http://localhost:3000/api/v1

**Create Agent:**
```bash
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agentType": "autonomous",
    "metadata": {
      "name": "My Agent",
      "description": "Agent description",
      "agentType": "autonomous"
    }
  }'
```

**List Agents:**
```bash
curl http://localhost:3000/api/v1/dids
```

**Dashboard Stats:**
```bash
curl http://localhost:3000/api/v1/dashboard/stats | jq
```

**Assign Role:**
```bash
curl -X POST http://localhost:3000/api/v1/rbac/roles/assign \
  -H "Content-Type: application/json" \
  -d '{
    "agentDID": "did:agent:YOUR_DID_HERE",
    "roleName": "agent:executor"
  }'
```

**Issue Credential:**
```bash
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subjectDID": "did:agent:YOUR_DID_HERE",
    "claims": {"role": "executor"},
    "expiresIn": "30d"
  }'
```

#### Gateway API
**Base URL:** http://localhost:8080

**Health Check:**
```bash
curl http://localhost:8080/health
```

---

### 🐳 Kubernetes Services

**View all pods:**
```bash
kubectl get pods -n agentos
```

**View logs:**
```bash
# Identity service logs
kubectl logs -n agentos -l app=identity -f

# Gateway logs
kubectl logs -n agentos -l app=gateway -f

# Web UI logs
kubectl logs -n agentos -l app=web-ui -f
```

**Check service status:**
```bash
kubectl get svc -n agentos
```

---

### 🛑 Stop Port Forwarding

To stop all port forwarding:
```bash
pkill -f "port-forward.*agentos"
```

To restart port forwarding:
```bash
kubectl port-forward -n agentos svc/web-ui 3001:80 &
kubectl port-forward -n agentos svc/identity 3000:3000 &
kubectl port-forward -n agentos svc/gateway 8080:8080 &
```

---

### 📊 Current Deployment

| Service | Status | URL | Port |
|---------|--------|-----|------|
| **Web UI** | ✅ Running | http://localhost:3001 | 3001→80 |
| **Identity** | ✅ Running | http://localhost:3000 | 3000→3000 |
| **Gateway** | ✅ Running | http://localhost:8080 | 8080→8080 |
| **PostgreSQL** | ✅ Running | - | 5432 |
| **Redis** | ✅ Running | - | 6379 |

---

### 🎯 Quick Start Guide

1. **Open Dashboard:** http://localhost:3001
2. **Create an Agent:** Use "Register Agent" page or API
3. **Assign a Role:** Use RBAC API endpoints
4. **View Dashboard:** See metrics update in real-time

---

### 🔧 Troubleshooting

**Port forwarding stopped?**
```bash
# Check if still running
ps aux | grep port-forward

# Restart
pkill -f "port-forward.*agentos"
kubectl port-forward -n agentos svc/web-ui 3001:80 &
```

**Can't access dashboard?**
```bash
# Check if web-ui pod is running
kubectl get pods -n agentos -l app=web-ui

# Check logs
kubectl logs -n agentos -l app=web-ui
```

**Database issues?**
```bash
# Connect to PostgreSQL
kubectl exec -it -n agentos deployment/postgres -- psql -U postgres -d agentos

# Check tables
\dt
```

---

### 📝 Example Workflow

```bash
# 1. Create an agent
RESPONSE=$(curl -s -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{"agentType":"autonomous","metadata":{"name":"Test Agent","agentType":"autonomous"}}')

# 2. Extract DID
DID=$(echo $RESPONSE | jq -r '.did.id')
echo "Created agent: $DID"

# 3. Assign role
curl -X POST http://localhost:3000/api/v1/rbac/roles/assign \
  -H "Content-Type: application/json" \
  -d "{\"agentDID\":\"$DID\",\"roleName\":\"agent:executor\"}"

# 4. Issue credential
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d "{\"subjectDID\":\"$DID\",\"claims\":{\"role\":\"executor\"},\"expiresIn\":\"30d\"}"

# 5. Check dashboard
open http://localhost:3001
```

---

**Your Agent Economy OS is fully operational!** 🎉
