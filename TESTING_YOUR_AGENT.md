# Testing Your Meal Planning Agent

## ✅ Current Status

**Database:** ✅ Enhanced schema loaded (8 agent tables + 2 views)  
**Runtime Service:** ✅ Running on http://localhost:8000  
**Your Agent:** ✅ Ready at `/Users/upalc/AgentOS/agentos/testAgents/agent.py`  
**V2 API:** ⚠️ Needs service restart to activate  

---

## 🚀 Quick Test (Works Now)

The enhanced database schema is loaded! To use the V2 API with full features:

### **Step 1: Restart Runtime Service**

```bash
# Find and stop current service
ps aux | grep "python -m src.main"
kill <PID>

# Or simpler:
killall -9 Python

# Start with V2 API
cd /Users/upalc/AgentOS/agentos/services/runtime
python -m src.main
```

**You should see:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
2025-10-27 22:45:00 - src.main - INFO - Starting Runtime service
2025-10-27 22:45:00 - src.database - INFO - Database connection pool established
2025-10-27 22:45:00 - src.main - INFO - Runtime service ready
2025-10-27 22:45:00 - src.main - INFO - V2 API routes registered  ← Should see this!
INFO:     Application startup complete.
```

### **Step 2: Test Your Agent with V2 API**

```bash
# In a new terminal
cd /Users/upalc/AgentOS/agentos/services/runtime
python deploy_test_agent_v2.py
```

**Expected Output:**
```
🚀 AgentOS Model A Deployment Test (Enhanced API)

[STEP 1] CREATE MODEL A AGENT
✅ Agent created successfully!
   Agent ID: 550e8400-...
   Deployment ID: ...
   
[STEP 2] UPLOAD ARTIFACT
✅ Code deployed

[STEP 3] GET AGENT DETAILS  
✅ Agent details retrieved
   Name: meal-planner-v2
   Model Type: A
   Status: RUNNING
   
[STEP 4] TEST INVOCATIONS
Test 1/4: Balanced Breakfast for 2
   ✅ Status: SUCCESS
   Recommendation: Oatmeal with berries and nuts
   Calories: 640
   Execution: 15ms
   Cost: $0.0100
   
[Complete with 4 test cases...]

[STEP 5] GET AGENT METRICS
✅ Metrics retrieved
   Total Invocations: 4
   Successful: 4
   P50 Latency: 14.00ms
   P95 Latency: 16.00ms
   
[STEP 6] GET COST BREAKDOWN
✅ Cost breakdown retrieved
   Total Cost: $0.0400
   Cost per Invocation: $0.0100
```

---

## 🔍 Verify Everything is Working

### **Check Service is Running:**
```bash
curl http://localhost:8000/
# Should return: {"service": "runtime-service", "version": "1.0.0", ...}
```

### **Check V2 API is Active:**
```bash
curl http://localhost:8000/docs
# Open in browser - should see /v1/agents/modelA endpoint
```

### **Check Database:**
```bash
docker exec agentos-postgres psql -U postgres -d agentos -c "\dt agent*"
# Should show: agents, agent_versions, agent_invocations, etc.
```

---

## 📊 Query Your Deployed Agents

### **After running deploy_test_agent_v2.py:**

```bash
# View all agents
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT id, name, model_type, status, runtime, created_at 
FROM agents 
ORDER BY created_at DESC;
"

# View invocations
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    i.agent_id,
    a.name as agent_name,
    i.status,
    i.execution_time_ms,
    i.cost_decimal,
    i.started_at
FROM invocations i
JOIN agents a ON i.agent_id = a.id
ORDER BY i.started_at DESC
LIMIT 10;
"

# View metrics
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    agent_id,
    name,
    total_invocations,
    successful_invocations,
    avg_execution_time_ms,
    total_cost_usd
FROM agent_stats_v2;
"
```

---

## 🎯 Test with OpenTelemetry Tracing

### **Option 1: Console Export (Simple)**

Edit `/Users/upalc/AgentOS/agentos/services/runtime/src/main.py` line 43:
```python
enable_console_export=True  # Change to True
```

Restart service. You'll see traces in console:
```json
{
  "name": "agent.invoke",
  "context": {
    "trace_id": "0x4bf92f3577b34da6a3ce929d0e0e4736",
    "span_id": "0xa3ce929d0e0e4736"
  },
  "attributes": {
    "agent.id": "550e8400-...",
    "agent.model_type": "A",
    "status": "SUCCESS"
  },
  "start_time": "2025-10-27T22:45:00.123456Z",
  "end_time": "2025-10-27T22:45:00.138456Z"
}
```

### **Option 2: Jaeger (Visual)**

```bash
# Terminal 1: Start Jaeger
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 6831:6831/udp \
  jaegertracing/all-in-one:latest

# Terminal 2: Configure telemetry
# Edit src/main.py line 41-42:
#   jaeger_endpoint="http://localhost:14268/api/traces",
#   enable_console_export=False

# Restart service
python -m src.main

# Terminal 3: Deploy agent
python deploy_test_agent_v2.py

# View traces
open http://localhost:16686
# Select: runtime-service
# Find: agent.invoke operations
```

---

## 🧪 Test Salesforce Agentforce (If You Have Access)

```bash
curl -X POST http://localhost:8000/v1/agents/modelB \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "salesforce-sales-agent",
    "endpoint_url": "https://yourinstance.salesforce.com/services/data/v59.0/einstein/ai-foundation/agents/0Xx.../invoke",
    "auth": {
      "type": "bearer",
      "value": "YOUR_SALESFORCE_ACCESS_TOKEN"
    },
    "rate_limit": {
      "rps": 5.0,
      "burst": 10
    }
  }'

# Get agent_id from response, then invoke:
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -H "Authorization: Bearer test_token" \
  -d '{
    "input_data": {
      "message": "Show all high-priority opportunities"
    }
  }'
```

---

## 🎨 Your Meal Planning Agent Options

You have 3 options for your existing agent:

### **Option 1: Convert to Model A (Code Upload)**

Extract the core logic from your Streamlit app:

```python
# Create: meal_planner_core.py
meal_type = input_data.get('meal_type', 'lunch')
dietary = input_data.get('dietary', 'balanced')

# ... your meal recommendation logic ...

result = {
    'recommendation': recommendation,
    'nutrition': {...},
    'cost_estimate': {...}
}
```

Upload via V2 API → Runs on AgentOS infrastructure

### **Option 2: Keep Streamlit, Register as Model B**

Keep your Streamlit app running locally:
```bash
cd /Users/upalc/AgentOS/agentos/testAgents
streamlit run agent.py  # Runs on port 8501
```

Register with AgentOS:
```bash
curl -X POST http://localhost:8000/v1/agents/modelB \
  -d '{
    "name": "streamlit-meal-planner",
    "endpoint_url": "http://localhost:8501/...",  # Your Streamlit endpoint
    "auth": {"type": "none"}
  }'
```

### **Option 3: Hybrid - Both!**

- Use Streamlit UI for interactive exploration
- Use AgentOS API for programmatic access
- Best of both worlds!

---

## 📈 Monitor Your Test Agent

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python monitor_agent.py
```

**Output:**
```
====================================================================================================
AGENTOS MONITORING DASHBOARD - 2025-10-27 22:45:00
====================================================================================================

📊 ACTIVE AGENTS
   • meal-planner-v2
     Status: RUNNING | Deployed: 2025-10-27 22:45:00 | Memory: 512Mi | CPU: 500m

📈 INVOCATIONS (Last 1 Hour)
   • meal-planner-v2
     Invocations: 4 | Success: 4 (100.0%) | Errors: 0 | Timeouts: 0
     Avg Time: 14.5ms | Total Cost: $0.0400

⚡ PERFORMANCE METRICS
   • meal-planner-v2
     Samples: 4 | Avg: 14.5ms | P50: 14ms | P95: 16ms | P99: 16ms
     Min: 13ms | Max: 17ms

💰 COST ANALYSIS
   Total Cost (24h): $0.0400

   • meal-planner-v2
     Invocations: 4 | Total: $0.0400 | Avg: $0.0100
```

---

## ✅ Success Checklist

After running everything, you should see:

- [ ] Runtime service started with "V2 API routes registered" log
- [ ] `deploy_test_agent_v2.py` completes successfully
- [ ] Agent created in database (`SELECT * FROM agents;`)
- [ ] 4 successful invocations logged
- [ ] Metrics show 100% success rate
- [ ] Cost tracking working ($0.01 per invocation)
- [ ] Monitor dashboard shows real-time stats

---

## 🐛 Troubleshooting

### **"404 Not Found" on /v1/agents/modelA**

**Solution:** Service needs restart
```bash
killall Python  # Stop all Python processes
cd services/runtime
python -m src.main  # Start fresh
```

### **Import Errors**

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### **Database Connection Failed**

**Solution:** Check PostgreSQL
```bash
docker ps | grep agentos-postgres
# If not running:
docker start agentos-postgres
```

### **Traces Not Showing**

**Solution:** Enable console export first
```python
# In src/main.py line 43:
enable_console_export=True
```

---

## 📚 Next Steps

1. ✅ **Test your agent** - Run deploy_test_agent_v2.py
2. ✅ **View metrics** - Run monitor_agent.py
3. ✅ **Query database** - See all invocations
4. ⚡ **Add Jaeger** - Visualize distributed traces
5. 🔐 **Test RBAC** - Start OPA and test permissions
6. 🌐 **Register Salesforce** - If you have Agentforce access

**You have a complete enterprise agent platform! 🎉**
