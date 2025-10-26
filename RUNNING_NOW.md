# Agent Economy OS - Currently Running! 🚀

## System Status: LIVE ✓

Your Agent Economy OS is now fully deployed and running!

---

## Access Points

### Web UI (Main Application)
**URL**: http://localhost:3004

**What you'll see:**
- ✓ Professional sidebar with navigation
- ✓ Dashboard with stats and charts
- ✓ Deploy Agent page
- ✓ All navigation pages accessible
- ✓ Dark mode support
- ✓ Responsive design

### Runtime Service API
**URL**: http://localhost:8000
**Health Check**: http://localhost:8000/health
**API Docs**: http://localhost:8000/docs

**Status**: ✓ HEALTHY
```json
{
    "status": "healthy",
    "service": "runtime-service",
    "timestamp": "2025-10-26T19:52:04.625450",
    "checks": {
        "database": true,
        "executor": true
    }
}
```

---

## Quick Test

### 1. Deploy an Agent via UI

1. Open http://localhost:3004
2. Click "Deploy Agent" in the sidebar
3. Fill in the form:
   - **Agent ID**: `my-first-agent`
   - **Code**:
     ```python
     result = input_data['x'] + input_data['y']
     ```
   - **Max Memory**: 512m
   - **Max CPU**: 0.5
4. Click "Deploy Agent"
5. See success message with deployment ID

### 2. Deploy an Agent via API

```bash
curl -X POST http://localhost:8000/api/v1/agents/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math-agent",
    "code": "result = input_data[\"x\"] * input_data[\"y\"]",
    "requirements": [],
    "environment": null,
    "max_memory": "512m",
    "max_cpu": "0.5"
  }'
```

### 3. Invoke an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math-agent",
    "input_data": {"x": 10, "y": 20},
    "timeout": 30
  }'
```

Expected output: `{"invocation_id":"...","status":"SUCCESS","output":200,...}`

### 4. Check Agent Status

```bash
curl http://localhost:8000/api/v1/agents/math-agent/status
```

---

## What's Running

### Kubernetes Pods
```
NAME                        READY   STATUS    RESTARTS   AGE
gateway-555c9f9d97-k7ln4    1/1     Running   0          4h+
identity-799f45f688-cv2s6   1/1     Running   0          4h+
postgres-545c64cd5f-kwqgn   1/1     Running   0          15m
redis-85864b4ccd-q6bp2      1/1     Running   0          14h+
runtime-68487844c8-k9jsv    1/1     Running   0          3m
web-ui-55c776974-nbvdj      1/1     Running   0          4h+
```

### Port Forwards
- **Runtime Service**: localhost:8000 → runtime:8000 (K8s)
- **Web UI**: localhost:3004 (local npm dev server)

### Database
- **PostgreSQL**: Running in K8s cluster
- **Tables Created**:
  - agent_deployments
  - agent_invocations
  - agent_metrics
- **Migration**: ✓ Completed

---

## UI Features Available

### Navigation (Sidebar)
- ✓ Dashboard - Main overview with stats
- ✓ Agents - Agent management (placeholder)
- ✓ Deployments - Track deployments (placeholder)
- ✓ Invocations - View execution history (placeholder)
- ✓ Logs - System logs (placeholder)
- ✓ Metrics - Performance metrics (placeholder)
- ✓ Settings - Configuration (placeholder)

### Dashboard
- ✓ 4 Stat Cards (Total Agents, Deployments, Invocations, Cost)
- ✓ 2 Chart Cards with beautiful visualizations
- ✓ Recent Invocations table with status badges
- ✓ Quick action buttons

### Deploy Agent
- ✓ Full deployment form
- ✓ Code editor with syntax hints
- ✓ Resource limit selection
- ✓ Loading states
- ✓ Success/error feedback

---

## Monitoring Commands

### Check All Pods
```bash
kubectl get pods -n agentos
```

### View Runtime Logs
```bash
kubectl logs -n agentos -l app=runtime -f
```

### View PostgreSQL Logs
```bash
kubectl logs -n agentos -l app=postgres -f
```

### Check Services
```bash
kubectl get svc -n agentos
```

### Describe Runtime Pod
```bash
kubectl describe pod -n agentos -l app=runtime
```

---

## Stop/Restart Commands

### Stop Port Forwards
```bash
# Find port forward processes
ps aux | grep "kubectl port-forward"

# Kill all port forwards
pkill -f "kubectl port-forward"
```

### Stop UI
```bash
# Find npm process
ps aux | grep "npm run dev"

# Or just
lsof -ti:3004 | xargs kill -9
```

### Restart Runtime Service
```bash
kubectl rollout restart deployment/runtime -n agentos
```

### Restart PostgreSQL
```bash
kubectl rollout restart deployment/postgres -n agentos
```

---

## Troubleshooting

### UI Not Loading?
1. Check port: `lsof -i:3004`
2. Clear cache: Cmd+Shift+R in browser
3. Check console: F12 → Console tab

### API Not Responding?
1. Check health: `curl http://localhost:8000/health`
2. Check port forward: `ps aux | grep port-forward`
3. Restart: `pkill -f port-forward` then re-run

### Database Issues?
1. Check pod: `kubectl get pods -n agentos -l app=postgres`
2. Check logs: `kubectl logs -n agentos -l app=postgres`
3. Port forward: `kubectl port-forward -n agentos svc/postgres 5432:5432`
4. Test: `PGPASSWORD=changeme123 psql -h localhost -U agentos -d agentos -c "SELECT 1"`

---

## Clean Up (When Done)

### Stop Everything
```bash
# Stop port forwards
pkill -f "kubectl port-forward"

# Stop UI
lsof -ti:3004 | xargs kill -9

# Delete K8s resources
kubectl delete -f k8s/08-runtime.yaml
kubectl delete deployment postgres -n agentos
kubectl delete svc postgres -n agentos
```

### Complete Cleanup
```bash
# Delete entire namespace (removes all resources)
kubectl delete namespace agentos
```

---

## Next Steps

### Immediate
1. ✓ Open UI at http://localhost:3004
2. ✓ Deploy your first agent
3. ✓ Test agent invocation
4. ✓ View dashboard updates

### Explore
- Check API docs: http://localhost:8000/docs
- Try different agent code
- Test error handling
- Monitor execution times
- View cost tracking

### Develop
- Connect Dashboard to real API data
- Build Agents management page
- Add real-time updates
- Implement search
- Add notifications

---

## System Architecture

```
┌─────────────────────────────────────┐
│   Browser (http://localhost:3004)   │
│          Web UI (React)              │
└──────────────┬──────────────────────┘
               │ HTTP/REST
               ▼
┌─────────────────────────────────────┐
│   Kubernetes Cluster (docker-desktop)│
│                                      │
│  ┌────────────┐    ┌─────────────┐ │
│  │  Runtime   │◄───┤  PostgreSQL │ │
│  │  Service   │    │             │ │
│  │ (FastAPI)  │    │  (Database) │ │
│  └────────────┘    └─────────────┘ │
│         ▲                            │
│         │ Port Forward (8000)        │
└─────────┼──────────────────────────┘
          │
     localhost:8000
```

---

## Success! 🎉

Your Agent Economy OS is fully operational:

- ✓ Runtime Service deployed and healthy
- ✓ PostgreSQL running with schema
- ✓ Web UI running and accessible
- ✓ Port forwards active
- ✓ All components connected

**Start using it now at**: http://localhost:3004

---

**Have fun deploying agents!** 🚀
