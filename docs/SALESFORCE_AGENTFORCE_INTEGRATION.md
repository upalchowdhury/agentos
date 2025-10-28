# Salesforce Agentforce Integration Guide

Complete guide to registering and using Salesforce Einstein Agentforce agents with Agent Economy OS, including OpenTelemetry distributed tracing.

---

## Overview

**Salesforce Agentforce** is Einstein's AI agent platform that can:
- Access Salesforce CRM data
- Execute Salesforce actions (create records, update opportunities, etc.)
- Maintain conversation context
- Use pre-built industry-specific actions

**AgentOS Integration Benefits:**
- ✅ Unified API gateway for all agents
- ✅ RBAC and governance layer
- ✅ Cost tracking and monitoring
- ✅ Distributed tracing with OpenTelemetry
- ✅ Audit trail for compliance
- ✅ Rate limiting and quotas

---

## Prerequisites

1. **Salesforce Org** with Einstein Agentforce enabled
2. **Agentforce Agent** created in Salesforce Setup
3. **Connected App** with OAuth credentials
4. **API Access** enabled for your user

---

## Step 1: Get Salesforce Credentials

### Create Connected App

1. **In Salesforce Setup:**
   - Search for "App Manager"
   - Click "New Connected App"
   - Fill in:
     - **Connected App Name:** `AgentOS Integration`
     - **API Name:** `AgentOS_Integration`
     - **Contact Email:** your@email.com

2. **OAuth Settings:**
   - Enable OAuth Settings: ✓
   - Callback URL: `https://login.salesforce.com/services/oauth2/callback`
   - Selected OAuth Scopes:
     - Full access (full)
     - Perform requests at any time (refresh_token, offline_access)
   - Save and note your **Consumer Key** and **Consumer Secret**

3. **Get User Security Token:**
   - Go to Settings → Reset My Security Token
   - Copy token from email

### Find Your Agentforce Agent ID

```bash
# Query Salesforce API
curl "https://yourinstance.salesforce.com/services/data/v59.0/einstein/ai-foundation/agents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response includes agent IDs (format: 0Xx...)
```

---

## Step 2: Register Agentforce with AgentOS

### Option A: Using Python SDK

```python
from services.runtime.src.agents.salesforce_proxy import SalesforceAgentBuilder

# Build registration payload
registration = SalesforceAgentBuilder.build_registration(
    name="salesforce-sales-agent",
    instance_url="https://mycompany.salesforce.com",
    agent_id="0Xx1234567890ABCDE",
    access_token="00D...!AR8AQ...",
    api_version="v59.0"
)

# Register with AgentOS
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/v1/agents/modelB",
        headers={"Authorization": "Bearer your_agentos_token"},
        json=registration
    )
    
    agent_id = response.json()["agent_id"]
    print(f"Registered Agentforce agent: {agent_id}")
```

### Option B: Using curl

```bash
curl -X POST http://localhost:8000/v1/agents/modelB \
  -H "Authorization: Bearer your_agentos_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "salesforce-sales-agent",
    "endpoint_url": "https://mycompany.salesforce.com/services/data/v59.0/einstein/ai-foundation/agents/0Xx1234567890ABCDE/invoke",
    "auth": {
      "type": "bearer",
      "value": "00D...!AR8AQ..."
    },
    "rate_limit": {
      "rps": 5.0,
      "burst": 10
    },
    "health_check_path": "/services/data/v59.0/einstein/ai-foundation/agents/0Xx1234567890ABCDE",
    "timeout_seconds": 30
  }'
```

### Option C: Using OAuth Password Flow

```python
from services.runtime.src.agents.salesforce_proxy import SalesforceAgentforceProxy

# Authenticate and create proxy
proxy = SalesforceAgentforceProxy.from_oauth(
    client_id="3MVG9...",
    client_secret="12345...",
    username="admin@company.com",
    password="mypassword",
    security_token="AbCdEfGhIjKlMnOp",
    instance_url="https://mycompany.salesforce.com",
    agent_id="0Xx1234567890ABCDE"
)

# Proxy is ready to use
result = await proxy.invoke({
    "message": "What's the status of opportunity 12345?"
})
```

---

## Step 3: Invoke Agentforce Agent

### Simple Invocation

```bash
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "message": "Show me all open opportunities for Acme Corp"
    }
  }'

# Response:
{
  "invocation_id": "550e8400-...",
  "agent_id": "...",
  "status": "SUCCESS",
  "result": {
    "message": "I found 5 open opportunities for Acme Corp...",
    "conversation_id": "abc123",
    "confidence": 0.95,
    "intent": "query_opportunities",
    "entities": [
      {"type": "Account", "name": "Acme Corp"}
    ],
    "actions_taken": [
      {"type": "query", "sobject": "Opportunity"}
    ]
  },
  "execution_time_ms": 1250,
  "cost": 0.02,
  "metadata": {
    "provider": "salesforce",
    "product": "agentforce"
  }
}
```

### With Conversation Context

```bash
# First message
CONVERSATION_ID=$(curl -s ... | jq -r '.result.conversation_id')

# Follow-up message (maintains context)
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -H "Authorization: Bearer your_token" \
  -d '{
    "input_data": {
      "message": "Update the largest opportunity to close won",
      "conversation_id": "'$CONVERSATION_ID'"
    }
  }'
```

### With User Context (for CRM data access)

```bash
curl -X POST http://localhost:8000/v1/agents/{agent_id}/invoke \
  -d '{
    "input_data": {
      "message": "Show my assigned leads",
      "user_context": {
        "user_id": "005...",
        "role": "Sales Rep",
        "region": "West"
      }
    }
  }'
```

---

## Step 4: Monitor with OpenTelemetry

### Start Jaeger (for viewing traces)

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

**Access Jaeger UI:** `http://localhost:16686`

### Configure Runtime Service with OpenTelemetry

```python
# In services/runtime/src/main.py
from src.telemetry import init_telemetry, TelemetryConfig

# Add to startup
init_telemetry(TelemetryConfig(
    service_name="runtime-service",
    service_version="0.2.0",
    jaeger_endpoint="http://localhost:14268/api/traces",
    enable_console_export=False
))
```

### View Distributed Trace

1. **Open Jaeger UI:** `http://localhost:16686`
2. **Select Service:** `runtime-service`
3. **Find Operation:** `agent.invoke`
4. **Click on trace** to see:
   - User request → AgentOS gateway
   - RBAC check (OPA decision)
   - External call → Salesforce Agentforce
   - Salesforce internal operations
   - Response back through chain
   - Database writes (audit log)

**Example Trace:**
```
┌─ agent.invoke (1.5s) ─────────────────────────┐
│  ├─ opa.check_permission (50ms)               │
│  ├─ agent.external_call (1.2s)                │
│  │  └─ HTTP POST to Salesforce (1.18s)        │
│  │     ├─ Salesforce Einstein (800ms)         │
│  │     └─ SOQL Query (200ms)                  │
│  └─ db.record_invocation (100ms)              │
└───────────────────────────────────────────────┘
```

---

## Step 5: Advanced Features

### A2A: Agentforce Calls Another Agent

```python
# Salesforce agent can invoke another AgentOS agent
# Set up A2A permission in OPA first

result = await agentforce_proxy.invoke({
    "message": "Process customer data with ML agent",
    # AgentOS automatically handles routing
})

# Trace shows:
# User → Agentforce → AgentOS Gateway → ML Agent → Response
```

### Get Agentforce Metadata

```python
from src.agents.salesforce_proxy import SalesforceAgentforceProxy

proxy = SalesforceAgentforceProxy(
    instance_url="https://mycompany.salesforce.com",
    agent_id="0Xx...",
    access_token="..."
)

# Get agent capabilities
metadata = await proxy.get_agent_metadata()
print(metadata)
# {
#   "name": "Sales Agent",
#   "description": "Helps with sales processes",
#   "capabilities": [...],
#   "supported_actions": [...]
# }

# List available actions
actions = await proxy.list_available_actions()
for action in actions:
    print(f"- {action['name']}: {action['description']}")
```

### Retrieve Conversation History

```python
history = await proxy.get_conversation_history(
    conversation_id="abc123",
    limit=20
)

for message in history:
    print(f"{message['role']}: {message['content']}")
```

---

## OpenTelemetry Metrics

### Available Metrics

**Counters:**
- `agent.invocations.total{agent.id, model_type, status, provider}`
- `agent.errors.total{agent.id, model_type, provider}`

**Histograms:**
- `agent.invocation.duration{agent.id, model_type, provider}` (in ms)
- `agent.invocation.cost{agent.id, model_type, provider}` (in USD)

### Query Metrics (Prometheus format)

```bash
# Total invocations for Salesforce agents
agent_invocations_total{provider="salesforce"}

# Average latency
rate(agent_invocation_duration_sum{provider="salesforce"}[5m]) 
/ 
rate(agent_invocation_duration_count{provider="salesforce"}[5m])

# Error rate
rate(agent_errors_total{provider="salesforce"}[5m])
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Salesforce Agentforce Monitoring",
    "panels": [
      {
        "title": "Invocations per Minute",
        "targets": [{
          "expr": "rate(agent_invocations_total{provider=\"salesforce\"}[1m]) * 60"
        }]
      },
      {
        "title": "P95 Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, agent_invocation_duration{provider=\"salesforce\"})"
        }]
      },
      {
        "title": "Total Cost (USD)",
        "targets": [{
          "expr": "sum(agent_invocation_cost_sum{provider=\"salesforce\"})"
        }]
      }
    ]
  }
}
```

---

## Cost Tracking

### Salesforce Agentforce Pricing

Typical pricing (verify with Salesforce):
- **Message**: $0.02 per message
- **Action Execution**: $0.01 per action
- **API Calls**: Standard Salesforce API limits apply

### Track Costs in AgentOS

```bash
# Get cost breakdown
curl http://localhost:8000/v1/agents/{agent_id}/costs?period=monthly

# Response:
{
  "agent_id": "...",
  "period": "monthly",
  "total_cost_usd": 145.50,
  "invocations": 7275,
  "cost_per_invocation_usd": 0.02,
  "breakdown": {
    "salesforce_messages": 140.00,
    "salesforce_actions": 5.50,
    "gateway_overhead": 0.00
  }
}
```

---

## Security & Compliance

### RBAC for Agentforce Access

```bash
# Only allow specific users to invoke Salesforce agent
# OPA policy automatically checks permissions

# Denied example:
curl -X POST .../invoke \
  -H "Authorization: Bearer unauthorized_user_token"

# Response: 403 Forbidden
{
  "detail": "Access denied by RBAC policy",
  "deny_reason": "user_not_authorized"
}
```

### Audit Trail

All Salesforce Agentforce invocations are logged:

```sql
SELECT 
    invoked_at,
    requester_id,
    input_data->>'message' as message,
    output_data->>'intent' as detected_intent,
    output_data->>'actions_taken' as actions,
    cost_decimal,
    execution_time_ms
FROM invocations
WHERE agent_id = '...' -- Salesforce agent
ORDER BY invoked_at DESC;
```

### PII Redaction

```python
# OPA can enforce PII redaction for Salesforce data
# Configure in invoke_allow.rego:

pii_redaction_required if {
    input.agent.metadata.handles_pii == true
    input.subject.privacy_settings.pii_redaction == true
}
```

---

## Troubleshooting

### Authentication Errors

```bash
# Error: "Authentication failed: invalid_grant"
# Solution: Regenerate security token and update

# Get new token
curl -X POST https://login.salesforce.com/services/oauth2/token \
  -d "grant_type=password" \
  -d "client_id=..." \
  -d "client_secret=..." \
  -d "username=..." \
  -d "password=PASSWORD+SECURITY_TOKEN"
```

### Rate Limit Errors

```bash
# Error: 429 Too Many Requests
# Solution: Increase rate_limit config

curl -X PATCH http://localhost:8000/v1/agents/{agent_id} \
  -d '{
    "rate_limit": {
      "rps": 10.0,
      "burst": 20
    }
  }'
```

### Missing Traces

```bash
# Check OpenTelemetry configuration
curl http://localhost:8000/health

# Verify Jaeger is running
curl http://localhost:14268/api/traces

# Enable console export for debugging
# In telemetry config: enable_console_export=True
```

---

## Complete Example

```python
"""
Complete Salesforce Agentforce integration with OpenTelemetry
"""

import asyncio
import httpx
from src.agents.salesforce_proxy import SalesforceAgentforceProxy
from src.telemetry import get_tracer

async def main():
    # Create proxy
    proxy = SalesforceAgentforceProxy(
        instance_url="https://mycompany.salesforce.com",
        agent_id="0Xx1234567890ABCDE",
        access_token="00D...!AR8AQ..."
    )
    
    # Get tracer for distributed tracing
    tracer = get_tracer()
    
    # Invoke with tracing
    with tracer.trace_external_call(
        provider="salesforce",
        endpoint=proxy.endpoint_url,
        agent_id="salesforce-sales-agent"
    ) as span:
        
        result = await proxy.invoke({
            "message": "Show all high-priority opportunities",
            "user_context": {
                "user_id": "005...",
                "role": "Sales Manager"
            }
        })
        
        # Add custom trace attributes
        span.set_attribute("result.confidence", result['result']['confidence'])
        span.set_attribute("result.intent", result['result']['intent'])
        span.set_attribute("actions.count", len(result['result']['actions_taken']))
        
        # Record metrics
        tracer.record_invocation_metrics(
            agent_id="salesforce-sales-agent",
            model_type="B",
            status="SUCCESS",
            duration_ms=result['metadata']['response_time_ms'],
            cost_usd=result['cost'],
            provider="salesforce"
        )
        
        print(f"Response: {result['result']['message']}")
        print(f"Cost: ${result['cost']}")
        print(f"Trace ID: {span.get_span_context().trace_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Summary

✅ **Salesforce Agentforce** fully supported via Model B  
✅ **OpenTelemetry** provides distributed tracing across all calls  
✅ **Cost tracking** for Salesforce messages and actions  
✅ **RBAC** controls who can invoke Agentforce agents  
✅ **Audit trail** captures all interactions for compliance  
✅ **Conversation context** maintained across messages  
✅ **CRM data access** through Salesforce's native permissions  

**Your Agentforce agents now have enterprise-grade observability and governance!** 🚀
