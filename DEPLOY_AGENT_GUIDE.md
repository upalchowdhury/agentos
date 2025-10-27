# Deploy Agent to AgentOS with RBAC, Logging & Security

This guide walks you through deploying an agent to the AgentOS runtime system with complete monitoring of RBAC, logging, and security.

## Prerequisites

1. ✅ PostgreSQL running with schema loaded
2. ✅ Runtime service configured
3. ✅ Agent code ready to deploy

## Step 1: Start the Runtime Service with Enhanced Logging

First, let's configure the runtime service with structured logging and RBAC:

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime

# Create .env with proper configuration
cat > .env << 'EOF'
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Service
DEBUG=true
HOST=0.0.0.0
PORT=8000
SERVICE_NAME=runtime-service

# Security
ENABLE_RBAC=true
LOG_LEVEL=DEBUG
EOF

# Start the service
python -m src.main
```

## Step 2: Load RBAC Schema

Ensure RBAC tables exist:

```bash
# Load RBAC schema
docker exec -i agentos-postgres psql -U postgres -d agentos < \
  /Users/upalc/AgentOS/agentos/infra/migrations/003_rbac_schema.sql
```

## Step 3: Create Agent Deployment Script

Create a deployment script with security and logging:

```python
# deploy_monitored_agent.py
import asyncio
import httpx
import json
from datetime import datetime

async def deploy_with_monitoring():
    base_url = "http://localhost:8000/api/v1/agents"
    
    # Your agent code (meal planning agent converted to AgentOS format)
    agent_code = """
# Simple meal recommendation agent
meal_type = input_data.get('meal_type', 'lunch')
dietary = input_data.get('dietary', 'balanced')

meals = {
    'breakfast': {
        'balanced': 'Oatmeal with berries and nuts',
        'vegetarian': 'Veggie scramble with toast',
        'low-carb': 'Greek yogurt with almonds'
    },
    'lunch': {
        'balanced': 'Quinoa bowl with chicken',
        'vegetarian': 'Lentil soup with salad',
        'low-carb': 'Grilled salmon with vegetables'
    },
    'dinner': {
        'balanced': 'Grilled chicken with rice',
        'vegetarian': 'Vegetable curry with quinoa',
        'low-carb': 'Steak with roasted vegetables'
    }
}

recommendation = meals.get(meal_type, {}).get(dietary, 'Healthy mixed salad')

result = {
    'meal_type': meal_type,
    'dietary_preference': dietary,
    'recommendation': recommendation,
    'timestamp': str(datetime.utcnow())
}
"""
    
    # Deployment payload
    deploy_payload = {
        "agent_id": "meal-planner-agent",
        "code": agent_code,
        "requirements": [],
        "environment": {
            "LOG_LEVEL": "INFO",
            "AGENT_TYPE": "meal_planner"
        },
        "max_memory": "256m",
        "max_cpu": "0.25"
    }
    
    print("=" * 80)
    print("DEPLOYING AGENT WITH SECURITY & LOGGING MONITORING")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Agent ID: {deploy_payload['agent_id']}")
    print(f"Memory Limit: {deploy_payload['max_memory']}")
    print(f"CPU Limit: {deploy_payload['max_cpu']}")
    print()
    
    async with httpx.AsyncClient() as client:
        # Deploy agent
        print("[1] DEPLOYING AGENT...")
        deploy_response = await client.post(
            f"{base_url}/deploy",
            json=deploy_payload,
            timeout=30.0
        )
        
        if deploy_response.status_code != 200:
            print(f"❌ Deployment failed: {deploy_response.status_code}")
            print(deploy_response.text)
            return
        
        deploy_result = deploy_response.json()
        deployment_id = deploy_result['deployment_id']
        
        print(f"✅ Deployment successful!")
        print(f"   Deployment ID: {deployment_id}")
        print(f"   Status: {deploy_result['status']}")
        print()
        
        # Test invocations with different scenarios
        test_cases = [
            {"meal_type": "breakfast", "dietary": "balanced"},
            {"meal_type": "lunch", "dietary": "vegetarian"},
            {"meal_type": "dinner", "dietary": "low-carb"},
        ]
        
        print("[2] TESTING AGENT INVOCATIONS...")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test_case}")
            
            invoke_response = await client.post(
                f"{base_url}/invoke",
                json={
                    "agent_id": "meal-planner-agent",
                    "input_data": test_case,
                    "timeout": 10
                },
                timeout=30.0
            )
            
            if invoke_response.status_code == 200:
                result = invoke_response.json()
                print(f"   ✅ Status: {result['status']}")
                print(f"      Output: {result['output']}")
                print(f"      Execution: {result['execution_time_ms']}ms")
                print(f"      Cost: {result['cost_cents']} cents")
            else:
                print(f"   ❌ Invocation failed: {invoke_response.status_code}")
        
        # Check agent status
        print("\n[3] CHECKING AGENT STATUS...")
        status_response = await client.get(
            f"{base_url}/meal-planner-agent/status",
            timeout=30.0
        )
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   ✅ Agent Status: {status['status']}")
            print(f"      Total Invocations: {status['invocation_count']}")
            print(f"      Last Invocation: {status.get('last_invocation', 'N/A')}")
        
        print("\n" + "=" * 80)
        print("DEPLOYMENT & TESTING COMPLETE")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. Check server logs for detailed execution traces")
        print("2. Query database for RBAC audit logs")
        print("3. Monitor metrics in observability dashboard")

if __name__ == "__main__":
    asyncio.run(deploy_with_monitoring())
```

## Step 4: Run Deployment with Monitoring

**Terminal 1** - Start Runtime Service:
```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python -m src.main
```

**Terminal 2** - Deploy Agent:
```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python deploy_monitored_agent.py
```

## Step 5: Monitor Security & RBAC

### Check RBAC Audit Logs

```bash
# View agent access logs
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    al.timestamp,
    al.agent_did,
    al.action,
    al.resource,
    al.status,
    r.name as role_name
FROM agent_audit_logs al
LEFT JOIN roles r ON al.role_id = r.id
ORDER BY al.timestamp DESC
LIMIT 20;
"
```

### Check Deployment Records

```bash
# View all agent deployments
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    id,
    agent_did,
    status,
    deployed_at,
    resource_limits->>'max_memory' as memory,
    resource_limits->>'max_cpu' as cpu
FROM agent_deployments
ORDER BY deployed_at DESC;
"
```

### Check Invocation Logs

```bash
# View agent invocations with metrics
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    agent_did,
    status,
    execution_time_ms,
    cost_cents,
    invoked_at,
    CASE WHEN error_message IS NOT NULL THEN 'HAS_ERROR' ELSE 'OK' END as error_status
FROM agent_invocations
WHERE agent_did = 'meal-planner-agent'
ORDER BY invoked_at DESC
LIMIT 10;
"
```

### Monitor Security Events

```bash
# Check for failed access attempts (RBAC violations)
docker exec agentos-postgres psql -U postgres -d agentos -c "
SELECT 
    timestamp,
    agent_did,
    action,
    status,
    metadata->>'error' as error_reason
FROM agent_audit_logs
WHERE status = 'denied'
ORDER BY timestamp DESC
LIMIT 10;
"
```

## Step 6: Enhanced Structured Logging

Add structured JSON logging for better monitoring. Create `services/runtime/src/logging_config.py`:

```python
import json
import logging
import sys
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "runtime-service",
        }
        
        # Add extra fields
        if hasattr(record, 'agent_id'):
            log_data['agent_id'] = record.agent_id
        if hasattr(record, 'deployment_id'):
            log_data['deployment_id'] = record.deployment_id
        if hasattr(record, 'invocation_id'):
            log_data['invocation_id'] = record.invocation_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add file/line info
        log_data['source'] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }
        
        return json.dumps(log_data)


def setup_structured_logging(log_level: str = "INFO"):
    """Setup structured JSON logging"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
```

Update `services/runtime/src/api/agents.py` to use structured logging:

```python
# Add to imports
import logging

logger = logging.getLogger(__name__)

# In deploy_agent function, replace simple logging:
logger.info(
    f"Deployed agent {request.agent_id}",
    extra={
        'agent_id': request.agent_id,
        'deployment_id': deployment_id,
        'action': 'deploy',
        'resource_limits': resource_limits
    }
)

# In invoke_agent function:
logger.info(
    f"Invoked agent {request.agent_id}",
    extra={
        'agent_id': request.agent_id,
        'invocation_id': invocation_id,
        'deployment_id': str(deployment_id),
        'action': 'invoke',
        'status': execution_result['status'],
        'execution_time_ms': execution_result['execution_time_ms']
    }
)
```

## Step 7: Real-time Monitoring Dashboard

Create a simple monitoring script:

```python
# monitor_agent.py
import asyncio
import psycopg2
from datetime import datetime, timedelta

def monitor_agents():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="agentos",
        user="postgres",
        password="postgres"
    )
    
    cur = conn.cursor()
    
    print("=" * 100)
    print(f"AGENTOS MONITORING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Active agents
    cur.execute("""
        SELECT agent_did, status, deployed_at
        FROM agent_deployments
        WHERE status = 'RUNNING'
        ORDER BY deployed_at DESC
    """)
    
    print("\n📊 ACTIVE AGENTS:")
    for row in cur.fetchall():
        print(f"   • {row[0]} - Status: {row[1]} - Deployed: {row[2]}")
    
    # Recent invocations (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    cur.execute("""
        SELECT 
            agent_did,
            COUNT(*) as total,
            AVG(execution_time_ms) as avg_time,
            SUM(cost_cents) as total_cost
        FROM agent_invocations
        WHERE invoked_at > %s
        GROUP BY agent_did
    """, (one_hour_ago,))
    
    print("\n📈 INVOCATIONS (Last Hour):")
    for row in cur.fetchall():
        print(f"   • {row[0]}: {row[1]} calls, avg {row[2]:.0f}ms, ${row[3]/100:.2f}")
    
    # Error rate
    cur.execute("""
        SELECT 
            agent_did,
            COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
            COUNT(*) as total,
            ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'ERROR') / COUNT(*), 2) as error_rate
        FROM agent_invocations
        WHERE invoked_at > %s
        GROUP BY agent_did
        HAVING COUNT(*) FILTER (WHERE status = 'ERROR') > 0
    """, (one_hour_ago,))
    
    print("\n⚠️  ERROR RATES:")
    for row in cur.fetchall():
        print(f"   • {row[0]}: {row[1]}/{row[2]} ({row[3]}% error rate)")
    
    # RBAC audit (if table exists)
    try:
        cur.execute("""
            SELECT action, status, COUNT(*) as count
            FROM agent_audit_logs
            WHERE timestamp > %s
            GROUP BY action, status
            ORDER BY count DESC
        """, (one_hour_ago,))
        
        print("\n🔒 SECURITY AUDIT (Last Hour):")
        for row in cur.fetchall():
            status_icon = "✅" if row[1] == "allowed" else "🚫"
            print(f"   {status_icon} {row[0]}: {row[2]} attempts ({row[1]})")
    except:
        print("\n🔒 SECURITY AUDIT: RBAC tables not loaded yet")
    
    print("\n" + "=" * 100)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    monitor_agents()
```

Run it:
```bash
python monitor_agent.py
```

## Security Best Practices

### 1. Enable Authentication (Future)
```python
# Add to src/api/agents.py
from fastapi import Depends, HTTPException, Header

async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.replace("Bearer ", "")
    # Verify token with identity service
    return token

@router.post("/deploy")
async def deploy_agent(request: DeploymentRequest, token: str = Depends(verify_token)):
    # Deployment logic with auth
    pass
```

### 2. Rate Limiting
```python
# Add to config.py
MAX_INVOCATIONS_PER_MINUTE = 100
MAX_DEPLOYMENTS_PER_HOUR = 10
```

### 3. Input Validation
Already implemented via Pydantic models in `src/models.py`.

## Summary

You now have:
- ✅ **Agent deployed** to AgentOS runtime
- ✅ **RBAC schema** for access control
- ✅ **Structured logging** with context
- ✅ **Database audit trails** for all operations
- ✅ **Monitoring dashboard** for real-time metrics
- ✅ **Security** event tracking

**Next Steps:**
1. Integrate with OpenTelemetry for distributed tracing
2. Set up Grafana dashboards for visualization
3. Configure alerts for errors and security events
4. Add authentication/authorization middleware
