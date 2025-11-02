# 🎯 AgentOS UI Complete Flow Guide

## ✅ What's Working Now

Your complete observability platform is deployed and operational!

---

## 🌐 Access Your Dashboard

**Main UI:** http://localhost:30080

---

## 🔄 Complete Flow

### 1. **Agent is Pre-Registered**

The Model B Test Agent is already deployed and running in Kubernetes:
- **Agent ID:** `550e8400-e29b-41d4-a716-446655440000`
- **Name:** `model-b-test-agent`
- **Endpoint:** `http://test-agent:9000` (internal K8s service)
- **Status:** ✅ Running

### 2. **Invoke Agent from UI**

Click the **"Invoke Test Agent"** button in the sidebar:

1. **UI sends request** → `/test-agent/invoke` (proxied by nginx)
2. **Nginx forwards** → `test-agent:9000/invoke` (K8s internal)
3. **Agent processes** → Returns result
4. **Agent sends telemetry** → ATP Ingest service
5. **Ingest stores** → PostgreSQL database
6. **UI auto-refreshes** → Shows new trace in 5-6 seconds

---

## 📊 What You'll See

### **Dashboard Metrics** (Updates every 10 seconds)
- **Total Invocations** - Increments with each call
- **Active Agents** - Shows 1 (model-b-test-agent)
- **Avg Latency** - ~200ms per invocation
- **Total Cost** - $0.05 per invocation

### **Recent Invocations Table**
New row appears showing:
- **Trace ID** - Unique trace identifier (first 8 chars)
- **Agent** - "model-b-test-agent"
- **Time** - Local time of invocation
- **Duration** - ~200ms
- **Status** - SUCCESS (green badge)
- **Cost** - $0.05
- **View** - Link to Jaeger trace details

---

## 🎯 Test the Complete Flow

### **Option 1: Use the UI Button**
```bash
1. Open http://localhost:30080
2. Click "Invoke Test Agent" in sidebar
3. Wait 5-6 seconds
4. See new trace appear in table
5. Click "View" to see in Jaeger
```

### **Option 2: Direct API Call**
```bash
# Invoke through UI proxy
curl -X POST http://localhost:30080/test-agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":{"test":"api_call"}}'

# Wait for telemetry
sleep 6

# View in observability API
curl -s "http://localhost:30003/v1/traces?limit=1" | jq
```

### **Option 3: Multiple Invocations**
```bash
# Generate 5 traces
for i in {1..5}; do
  curl -s -X POST http://localhost:30080/test-agent/invoke \
    -H "Content-Type: application/json" \
    -d '{"input":{"batch":"test-'$i'"}}'
  sleep 2
done

# Dashboard will update automatically
```

---

## 🔍 View Traces & Logs

### **In Dashboard** (http://localhost:30080)
- Auto-updates every 10 seconds
- Shows last 20 traces
- Click "Refresh" for manual update
- Click "View" on any trace → Opens in Jaeger

### **In Jaeger** (http://localhost:31686)
- Click sidebar link or trace "View" button
- Search by service: "agentos"
- View full trace timeline with spans
- See detailed step information

### **In Grafana** (http://localhost:31000)
- Login: admin/admin
- Create custom dashboards
- PostgreSQL datasource pre-configured
- Query invocations table directly

---

## 📡 Agent Registration Flow

Currently the test agent is pre-deployed and configured. To add new agents:

### **Step 1: Deploy Agent to K8s**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-new-agent
  namespace: agentos
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: agent
        image: my-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: ATP_INGEST_URL
          value: "http://ingest:8001"
---
apiVersion: v1
kind: Service
metadata:
  name: my-new-agent
  namespace: agentos
spec:
  ports:
  - port: 8080
  selector:
    app: my-new-agent
```

### **Step 2: Agent Sends ATP Telemetry**
```python
# Your agent should send this format to ATP_INGEST_URL
{
  "trace": {
    "trace_id": "<uuid>",
    "invocation_id": "<uuid>",
    "agent_id": "<your-agent-uuid>",
    "protocol": "http",
    "status": "success",
    "start_ts": "2025-11-02T20:00:00Z",
    "end_ts": "2025-11-02T20:00:01Z",
    "execution_time_ms": 1000,
    "cost_cents": 10
  },
  "steps": [...]
}
```

### **Step 3: Update UI Proxy** (if needed for direct invocation)
Add to nginx config in `infra/k8s/web-ui.yaml`:
```nginx
location /my-agent/ {
    proxy_pass http://my-new-agent:8080/;
    ...
}
```

---

## 🎨 UI Features Explained

### **Sidebar Navigation**
- **Dashboard** - Main view with metrics & traces
- **Agents** - Agent management (coming soon)
- **Invocations** - Full history (coming soon)
- **Traces (Jaeger)** - External distributed tracing UI
- **Grafana** - External metrics dashboards
- **API Docs** - Swagger API explorer

### **"Invoke Test Agent" Button**
- Calls `/test-agent/invoke` through nginx proxy
- Nginx forwards to `test-agent:9000` (K8s service)
- Fallback: tries Runtime API if direct fails
- Shows success alert with trace ID
- Auto-refreshes dashboard after 6 seconds

### **Dark Mode Toggle**
- Click moon icon in top-right
- Persists during session
- Affects all UI components

### **Refresh Button**
- Manual data reload
- Fetches latest traces
- Updates all metrics

---

## 🧪 Verification Commands

### **Check All Services**
```bash
kubectl get pods -n agentos
# Should show 15 pods running
```

### **Test Agent Health**
```bash
# Through UI proxy
curl http://localhost:30080/test-agent/health

# Direct to service
kubectl exec -n agentos $(kubectl get pod -l app=test-agent -n agentos -o name | head -1) -- \
  curl -s http://localhost:9000/health
```

### **View Latest Traces**
```bash
curl -s "http://localhost:30003/v1/traces?limit=5" | jq
```

### **Check Telemetry Flow**
```bash
# 1. Invoke agent
TRACE_ID=$(curl -s -X POST http://localhost:30080/test-agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":{"flow_test":"yes"}}' | jq -r '.trace_id')

echo "Trace ID: $TRACE_ID"

# 2. Wait for processing
sleep 8

# 3. Verify in database
kubectl exec postgres-0 -n agentos -- \
  psql -U postgres -d agentos -c \
  "SELECT metadata->>'trace_id', status, execution_time_ms FROM invocations ORDER BY started_at DESC LIMIT 1;"
```

---

## 🏗️ Architecture Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ http://localhost:30080
       ▼
┌─────────────────────┐
│   Web UI (nginx)    │ ← HTML/CSS/JS Dashboard
│   - Dashboard       │
│   - Proxy /api/*    │ ──→ observability-api:8003
│   - Proxy /runtime/*│ ──→ runtime:8000
│   - Proxy /test-agent/*│ ──→ test-agent:9000
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Test Agent        │
│   (model-b-test)    │
│   Port: 9000        │
└──────┬──────────────┘
       │ ATP Telemetry
       ▼
┌─────────────────────┐
│   ATP Ingest        │ ──→ PostgreSQL
│   Port: 8001        │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Observability API  │ ←─── UI queries traces
│   Port: 8003        │
└─────────────────────┘
```

---

## ✨ Success Criteria

✅ **UI loads** - http://localhost:30080 shows dashboard  
✅ **Metrics display** - Shows current invocation count  
✅ **Button works** - "Invoke Test Agent" triggers successfully  
✅ **Telemetry flows** - Traces appear in table after 5-6 seconds  
✅ **Jaeger integration** - "View" links open correct traces  
✅ **Auto-refresh** - Dashboard updates every 10 seconds  
✅ **Dark mode** - Toggle works correctly  

---

## 🎉 Your Platform is Ready!

**Everything is deployed and working:**

1. ✅ Web UI with live data
2. ✅ Test agent deployed in K8s
3. ✅ ATP telemetry flowing
4. ✅ Traces stored in PostgreSQL
5. ✅ Observability API serving data
6. ✅ Jaeger UI for trace visualization
7. ✅ Grafana for custom dashboards

**Just open http://localhost:30080 and start clicking!** 🚀

---

## 📞 Quick Reference

| What | URL |
|------|-----|
| **Main Dashboard** | http://localhost:30080 |
| Jaeger Traces | http://localhost:31686 |
| Grafana Dashboards | http://localhost:31000 (admin/admin) |
| Observability API | http://localhost:30003/docs |
| Runtime API | http://localhost:30000/docs |

**Current Test Agent:**
- ID: `550e8400-e29b-41d4-a716-446655440000`
- Name: `model-b-test-agent`
- Endpoint: `http://test-agent:9000`
