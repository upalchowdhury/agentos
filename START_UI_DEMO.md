# 🎨 AgentOS UI Demo Guide

Complete guide to accessing all UI interfaces for your demo.

---

## 🚀 Quick Start - All UIs Available NOW

### 1. **Simple Dashboard** (No Build Required)
**Open:** http://localhost:3001/dashboard.html

This is a standalone HTML dashboard that shows:
- Real-time metrics (invocations, latency, cost)
- Recent traces table with live updates
- Quick links to other UIs

Just save the file and open in your browser!

---

### 2. **Jaeger UI** (Distributed Tracing) ✅ DEPLOYED
**URL:** http://localhost:31686

**Features:**
- Visual trace timeline
- Service dependencies
- Trace search and filtering
- Span details and logs

**How to use:**
1. Open http://localhost:31686
2. Select "agentos" from Service dropdown
3. Click "Find Traces"
4. Click any trace to see detailed timeline

---

### 3. **Grafana** (Dashboards & Metrics) ✅ DEPLOYED
**URL:** http://localhost:31000  
**Username:** `admin`  
**Password:** `admin`

**Features:**
- Custom dashboards
- PostgreSQL data source (pre-configured)
- Real-time metrics from Prometheus
- Alert configuration

**How to use:**
1. Open http://localhost:31000
2. Login with admin/admin
3. Go to Dashboards → New Dashboard
4. Add panel → Select PostgreSQL datasource
5. Query your invocations table

**Sample SQL Queries for Grafana:**
```sql
-- Total invocations over time
SELECT 
  $__timeGroup(started_at, '1m') as time,
  COUNT(*) as invocations
FROM invocations
WHERE $__timeFilter(started_at)
GROUP BY time
ORDER BY time

-- Average latency by agent
SELECT 
  a.name,
  AVG(i.execution_time_ms) as avg_latency
FROM invocations i
JOIN agents a ON i.agent_id = a.id
GROUP BY a.name

-- Cost tracking
SELECT 
  $__timeGroup(started_at, '1h') as time,
  SUM(cost_decimal) as total_cost
FROM invocations
WHERE $__timeFilter(started_at)
GROUP BY time
ORDER BY time
```

---

### 4. **Prometheus** (Metrics Backend) ✅ DEPLOYED
**URL:** http://localhost:31090

**Features:**
- Raw metrics queries
- Service health monitoring
- Target status

---

### 5. **API Documentation** (Swagger UI)

#### Observability API
**URL:** http://localhost:30003/docs
- View traces
- Get agent metrics
- Search functionality

#### Runtime API
**URL:** http://localhost:30000/docs
- Agent management
- Invocation endpoints
- Cost tracking

#### Test Agent
**URL:** http://localhost:9000/docs
- Invoke agent directly
- Test telemetry

---

## 🎬 Demo Flow

### Option 1: Quick Visual Demo (5 minutes)

1. **Show Real-time Dashboard**
   ```bash
   # Open in browser
   http://localhost:3001/dashboard.html
   ```

2. **Generate some traffic**
   ```bash
   # Run 10 invocations
   for i in {1..10}; do
     curl -s -X POST http://localhost:9000/invoke \
       -H "Content-Type: application/json" \
       -d '{"input":{"demo":"test-'$i'"}}' | jq -c '{trace_id, execution_time_ms}'
     sleep 1
   done
   ```

3. **Show Jaeger traces**
   - Open http://localhost:31686
   - Select "agentos" service
   - Show trace timeline and spans

4. **Show Grafana dashboard**
   - Open http://localhost:31000
   - Create quick dashboard with invocations query

---

### Option 2: Deep Dive Demo (15 minutes)

1. **Start with Architecture Overview**
   - Show Kubernetes pods: `kubectl get pods -n agentos`
   - Explain observability stack

2. **Live Agent Invocation**
   ```bash
   TRACE_ID=$(curl -s -X POST http://localhost:9000/invoke \
     -H "Content-Type: application/json" \
     -d '{"input":{"demo":"live"}}' | jq -r '.trace_id')
   
   echo "Trace ID: $TRACE_ID"
   sleep 5
   
   # Show in API
   curl "http://localhost:30003/v1/traces/$TRACE_ID" | jq
   ```

3. **Show in Jaeger**
   - Paste trace_id in Jaeger search
   - Show service dependencies
   - Explain span details

4. **Show Metrics in Grafana**
   - Create dashboard with time-series
   - Show cost tracking
   - Demonstrate alerting rules

5. **API Explorer**
   - Use Swagger UI to run queries
   - Show interactive documentation

---

## 🏗️ Build Full React UI (Optional)

If you want the full-featured React dashboard:

```bash
cd web-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

Then open: http://localhost:3001

**Features in React UI:**
- Modern responsive design
- Real-time updates
- Advanced filtering
- Agent management
- Cost analytics

---

## 📊 All Available URLs

| Service | URL | Status |
|---------|-----|--------|
| **Simple Dashboard** | http://localhost:3001/dashboard.html | 🟢 Ready |
| **Jaeger UI** | http://localhost:31686 | 🟢 Deployed |
| **Grafana** | http://localhost:31000 | 🟢 Deployed |
| **Prometheus** | http://localhost:31090 | 🟢 Deployed |
| **Observability API** | http://localhost:30003/docs | 🟢 Ready |
| **Runtime API** | http://localhost:30000/docs | 🟢 Ready |
| **Test Agent** | http://localhost:9000/docs | 🟢 Running |
| **React UI** | http://localhost:3001 | 🟡 Build Required |

---

## 🎯 Demo Checklist

### Before Demo
- [ ] All services running: `kubectl get pods -n agentos`
- [ ] Test agent running: `curl http://localhost:9000/health`
- [ ] Generate sample data: Run 5-10 test invocations
- [ ] Open all browser tabs
- [ ] Test Jaeger search
- [ ] Login to Grafana

### During Demo
- [ ] Show real-time dashboard
- [ ] Invoke agent live
- [ ] Show trace in Jaeger
- [ ] Show metrics in Grafana
- [ ] Explain ATP telemetry flow
- [ ] Show cost tracking

---

## 🔥 Quick Commands

```bash
# Check all services
kubectl get all -n agentos

# Invoke test agent
curl -X POST http://localhost:9000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":{"test":"data"}}'

# View recent traces
curl -s "http://localhost:30003/v1/traces?limit=5" | jq

# Generate load for demo
for i in {1..20}; do
  curl -s -X POST http://localhost:9000/invoke \
    -H "Content-Type: application/json" \
    -d '{"input":{"load_test":"'$i'"}}' > /dev/null
  sleep 0.5
done

# Check monitoring pods
kubectl get pods -n agentos | grep -E "(jaeger|grafana|prometheus)"
```

---

## 🆘 Troubleshooting

### Jaeger not showing traces
```bash
# Check Jaeger is running
kubectl logs -l app=jaeger -n agentos --tail=50

# Verify OTel bridge is configured
kubectl logs -l app=otel-bridge -n agentos --tail=20
```

### Grafana can't connect to PostgreSQL
```bash
# Test database connectivity
kubectl exec -it postgres-0 -n agentos -- psql -U postgres -d agentos -c "SELECT 1"

# Check Grafana logs
kubectl logs -l app=grafana -n agentos --tail=50
```

### Dashboard not updating
- Refresh browser (Ctrl+Shift+R)
- Check browser console for errors
- Verify API is accessible: `curl http://localhost:30003/v1/traces`

---

## 🎉 You're Ready to Demo!

**Start here:** http://localhost:3001/dashboard.html

Then explore:
- Jaeger: http://localhost:31686
- Grafana: http://localhost:31000
- APIs: http://localhost:30003/docs

**Generate demo data:**
```bash
./test-model-b.sh invoke 550e8400-e29b-41d4-a716-446655440000
```
