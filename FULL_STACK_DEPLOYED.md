# 🎉 AgentOS Full Stack Deployed on Kubernetes

**Complete observability platform with unified UI**

---

## 🌐 Access Your Dashboard

### **Main Web UI** (Your Enhanced Dashboard)
**URL:** http://localhost:30080

This is your complete AgentOS dashboard with:
- Real-time metrics
- Live invocations table
- Agent management
- Direct links to Jaeger & Grafana
- One-click agent invocation

---

## 📊 Complete Stack URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Web UI Dashboard** | http://localhost:30080 | Main UI - Start here! |
| **Jaeger Tracing** | http://localhost:31686 | Distributed tracing visualization |
| **Grafana Dashboards** | http://localhost:31000 | Metrics & custom dashboards |
| **Prometheus** | http://localhost:31090 | Metrics backend |
| **Observability API** | http://localhost:30003/docs | API documentation |
| **Runtime API** | http://localhost:30000/docs | Agent runtime API |
| **ATP Ingest** | http://localhost:30001/docs | Telemetry ingest API |
| **Test Agent** | http://localhost:9000/docs | Model B test agent |

---

## 🏗️ Deployed Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Browser / User                             │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ HTTP :30080
                       ▼
        ┌──────────────────────────────┐
        │       Web UI (Nginx)         │
        │    - Dashboard              │
        │    - Dark Mode              │
        │    - Live Updates           │
        └──────────────┬───────────────┘
                       │
        ┌──────────────┴───────────────┐
        │                              │
        ▼                              ▼
┌───────────────┐              ┌──────────────┐
│ Observability │              │  Runtime API │
│      API      │              │   :30000     │
│    :30003     │              └──────┬───────┘
└───────┬───────┘                     │
        │                             │
        │                             ▼
        │                      ┌──────────────┐
        │                      │  PostgreSQL  │
        │                      │  (Storage)   │
        │                      └──────────────┘
        │
        ▼
┌───────────────┐              ┌──────────────┐
│  ATP Ingest   │◄─────────────│ Test Agent   │
│    :30001     │  Telemetry   │   :9000      │
└───────┬───────┘              └──────────────┘
        │
        ▼
┌───────────────┐
│  PostgreSQL   │
│   Database    │
└───────────────┘

     Monitoring Layer
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│    Jaeger     │  │   Grafana    │  │ Prometheus   │
│   :31686      │  │   :31000     │  │   :31090     │
└───────────────┘  └──────────────┘  └──────────────┘
```

---

## ✅ All Services Running

Check status:
```bash
kubectl get pods -n agentos
```

Expected output:
```
NAME                                 READY   STATUS    
web-ui-xxxxx-xxxxx                   1/1     Running   ✅
runtime-xxxxx-xxxxx                  1/1     Running   ✅
ingest-xxxxx-xxxxx                   1/1     Running   ✅
observability-api-xxxxx-xxxxx        1/1     Running   ✅
otel-bridge-xxxxx-xxxxx              1/1     Running   ✅
jaeger-xxxxx-xxxxx                   1/1     Running   ✅
grafana-xxxxx-xxxxx                  1/1     Running   ✅
prometheus-xxxxx-xxxxx               1/1     Running   ✅
postgres-0                           1/1     Running   ✅
```

---

## 🎯 Quick Demo Flow

### 1. **Open Main Dashboard**
```bash
open http://localhost:30080
```

### 2. **Click "Invoke Test Agent"** 
- Button in sidebar
- Generates a test invocation
- Auto-refreshes after 5 seconds

### 3. **Watch Live Updates**
- Metrics update every 10 seconds
- New traces appear in table
- Click "View" to see in Jaeger

### 4. **Explore Other UIs**
- **Jaeger** - Click trace links or visit http://localhost:31686
- **Grafana** - Visit http://localhost:31000 (admin/admin)
- **API Docs** - Interactive Swagger at http://localhost:30003/docs

---

## 🔧 Features

### Web UI Dashboard
- ✅ Real-time metrics (invocations, agents, latency, cost)
- ✅ Live invocations table with auto-refresh
- ✅ Dark mode toggle
- ✅ One-click agent invocation
- ✅ Links to all monitoring tools
- ✅ Responsive design
- ✅ Material Design icons

### Observability Stack
- ✅ ATP v0 telemetry ingestion
- ✅ Distributed tracing with Jaeger
- ✅ Metrics with Prometheus & Grafana
- ✅ PostgreSQL persistence
- ✅ Cost tracking
- ✅ Agent performance analytics

### Integration
- ✅ All services on same cluster
- ✅ Internal networking configured
- ✅ Health checks enabled
- ✅ Auto-scaling ready
- ✅ Resource limits set

---

## 📈 Test Commands

### Generate Test Traffic
```bash
# Invoke agent 10 times
for i in {1..10}; do
  curl -s -X POST http://localhost:9000/invoke \
    -H "Content-Type: application/json" \
    -d '{"input":{"test":"load-'$i'"}}'
  sleep 1
done
```

### Check Service Health
```bash
# All services
kubectl get pods -n agentos

# Web UI logs
kubectl logs -l app=web-ui -n agentos --tail=50

# API health
curl http://localhost:30003/health
curl http://localhost:30000/health
curl http://localhost:30001/health
```

### View Database Data
```bash
kubectl exec -it postgres-0 -n agentos -- \
  psql -U postgres -d agentos -c \
  "SELECT COUNT(*), AVG(execution_time_ms)::int as avg_ms FROM invocations;"
```

---

## 🎨 UI Features Explained

### Dashboard Stats
1. **Total Invocations** - Count of all traces
2. **Active Agents** - Unique agents with invocations
3. **Avg Latency** - Average execution time
4. **Total Cost** - Sum of all invocation costs

### Recent Invocations Table
- **Trace ID** - First 8 chars (click View for full)
- **Agent** - Agent name from registration
- **Time** - Local time of invocation
- **Duration** - Execution time in milliseconds
- **Status** - SUCCESS or FAILED with color coding
- **Cost** - USD cost per invocation

### Navigation
- **Dashboard** - Main view (you're here)
- **Agents** - Agent management (coming soon)
- **Invocations** - Full history (coming soon)
- **Traces (Jaeger)** - External link to Jaeger UI
- **Grafana** - External link to Grafana
- **API Docs** - External link to Swagger UI

---

## 🔐 Service Networking

### Internal Communication (K8s)
```
web-ui → observability-api.agentos.svc.cluster.local:8003
observability-api → postgres.agentos.svc.cluster.local:5432
ingest → postgres.agentos.svc.cluster.local:5432
```

### External Access (NodePorts)
```
:30080 → web-ui (Main Dashboard)
:30000 → runtime
:30001 → ingest
:30003 → observability-api
:31000 → grafana
:31090 → prometheus
:31686 → jaeger
```

---

## 🚀 Scaling

### Scale Web UI
```bash
kubectl scale deploy web-ui -n agentos --replicas=3
```

### Scale Backend Services
```bash
kubectl scale deploy observability-api -n agentos --replicas=3
kubectl scale deploy ingest -n agentos --replicas=3
kubectl scale deploy runtime -n agentos --replicas=3
```

---

## 🛠️ Troubleshooting

### Web UI Not Loading
```bash
# Check pods
kubectl get pods -l app=web-ui -n agentos

# Check logs
kubectl logs -l app=web-ui -n agentos --tail=50

# Restart
kubectl rollout restart deploy web-ui -n agentos
```

### Data Not Showing
```bash
# Check observability API
curl http://localhost:30003/health

# Check if traces exist
curl http://localhost:30003/v1/traces?limit=5

# Generate test data
curl -X POST http://localhost:9000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":{"test":"debug"}}'
```

### Services Can't Communicate
```bash
# Check all services
kubectl get svc -n agentos

# Test connectivity
kubectl exec -it $(kubectl get pod -l app=web-ui -n agentos -o name | head -1) -n agentos -- \
  wget -O- http://observability-api:8003/health
```

---

## 📋 Complete Service Inventory

| Service | Pods | Port | NodePort | Status |
|---------|------|------|----------|--------|
| web-ui | 2 | 80 | 30080 | ✅ |
| runtime | 2 | 8000 | 30000 | ✅ |
| ingest | 2 | 8001 | 30001 | ✅ |
| observability-api | 2 | 8003 | 30003 | ✅ |
| otel-bridge | 1 | 8002 | - | ✅ |
| jaeger | 1 | 16686 | 31686 | ✅ |
| grafana | 1 | 3000 | 31000 | ✅ |
| prometheus | 1 | 9090 | 31090 | ✅ |
| postgres | 1 | 5432 | - | ✅ |

---

## 🎊 Success!

Your complete AgentOS platform is now running as a unified stack in Kubernetes!

**Start here:** http://localhost:30080

Everything works together:
- ✅ UI talks to APIs
- ✅ APIs talk to database
- ✅ Telemetry flows through system
- ✅ Monitoring tools integrated
- ✅ All services healthy

**Deploy complete! Time to demo! 🚀**
