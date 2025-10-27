# Expected Log Output - Agent Testing

This document shows what logs you should see when testing agent deployment.

## Terminal 1: Runtime Service Logs

When you run `python -m src.main`, you should see:

### Service Startup
```
2024-10-26 18:10:00,123 - src.config - INFO - Loading configuration
2024-10-26 18:10:00,234 - src.main - INFO - Starting Runtime service
2024-10-26 18:10:00,345 - src.database - INFO - Connecting to database at postgresql://postgres:***@localhost:5432/agentos
2024-10-26 18:10:00,456 - asyncpg.pool - INFO - Created connection pool
2024-10-26 18:10:00,567 - src.main - INFO - Runtime service ready
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### During Test Execution

#### 1. Agent Deployment
```
INFO:     127.0.0.1:54321 - "POST /api/v1/agents/deploy HTTP/1.1" 200 OK
2024-10-26 18:12:34,123 - src.api.agents - INFO - Deployed agent simple-calculator with deployment_id 550e8400-e29b-41d4-a716-446655440000
```

#### 2. Agent Invocations
```
INFO:     127.0.0.1:54322 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:12:35,234 - src.api.agents - INFO - Invoked agent simple-calculator, invocation_id abc123def456, status SUCCESS

INFO:     127.0.0.1:54323 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:12:35,345 - src.api.agents - INFO - Invoked agent simple-calculator, invocation_id def456ghi789, status SUCCESS

INFO:     127.0.0.1:54324 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:12:35,456 - src.api.agents - INFO - Invoked agent simple-calculator, invocation_id ghi789jkl012, status SUCCESS

INFO:     127.0.0.1:54325 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:12:35,567 - src.api.agents - INFO - Invoked agent simple-calculator, invocation_id jkl012mno345, status SUCCESS
```

#### 3. Status Check
```
INFO:     127.0.0.1:54326 - "GET /api/v1/agents/simple-calculator/status HTTP/1.1" 200 OK
```

## Terminal 2: Test Script Output

When you run `python test_simple_agent.py`, you should see:

```
============================================================
AGENT RUNTIME TEST - LOGGING VERIFICATION
============================================================

This script will:
  1. Deploy a simple calculator agent
  2. Invoke it with test calculations
  3. Check agent status

Watch the server logs for deployment and invocation messages!
============================================================

============================================================
DEPLOYING SIMPLE CALCULATOR AGENT
============================================================
Deploy Status: 200
Deployment ID: 550e8400-e29b-41d4-a716-446655440000
Status: RUNNING
Message: Agent deployed successfully

============================================================
TESTING CALCULATIONS
============================================================

[1] Testing: Add 5 + 3
    Status: SUCCESS
    Output: {'operation': 'add', 'inputs': {'a': 5, 'b': 3}, 'result': 8}
    Execution Time: 15ms
    Cost: 1 cents

[2] Testing: Multiply 4 * 7
    Status: SUCCESS
    Output: {'operation': 'multiply', 'inputs': {'a': 4, 'b': 7}, 'result': 28}
    Execution Time: 12ms
    Cost: 1 cents

[3] Testing: Subtract 10 - 3
    Status: SUCCESS
    Output: {'operation': 'subtract', 'inputs': {'a': 10, 'b': 3}, 'result': 7}
    Execution Time: 13ms
    Cost: 1 cents

[4] Testing: Divide 20 / 4
    Status: SUCCESS
    Output: {'operation': 'divide', 'inputs': {'a': 20, 'b': 4}, 'result': 5.0}
    Execution Time: 14ms
    Cost: 1 cents

============================================================
CHECKING AGENT STATUS
============================================================
Agent ID: simple-calculator
Status: RUNNING
Deployed At: 2024-10-26T18:12:34.123456
Total Invocations: 4
Last Invocation: 2024-10-26T18:12:35.567890

============================================================
TEST COMPLETED
============================================================

Check the server logs for these entries:
  - Deployed agent simple-calculator with deployment_id <uuid>
  - Invoked agent simple-calculator, invocation_id <uuid>, status SUCCESS
```

## Error Scenarios

### Agent Execution Error
**Terminal 1:**
```
2024-10-26 18:15:00,123 - src.agents.executor - ERROR - Agent calculator execution error: division by zero
INFO:     127.0.0.1:54327 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:15:00,234 - src.api.agents - INFO - Invoked agent calculator, invocation_id xyz789, status ERROR
```

**Terminal 2:**
```
[5] Testing: Divide 10 / 0
    Status: ERROR
    Output: None
    Execution Time: 5ms
    Cost: 1 cents
```

### Agent Timeout
**Terminal 1:**
```
2024-10-26 18:16:00,123 - src.agents.executor - WARNING - Agent slow-agent execution timed out
INFO:     127.0.0.1:54328 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:16:00,234 - src.api.agents - INFO - Invoked agent slow-agent, invocation_id uvw456, status TIMEOUT
```

**Terminal 2:**
```
[1] Testing: Long calculation
    Status: TIMEOUT
    Output: None
    Execution Time: 10000ms
    Cost: 10 cents
```

### Deployment Failure
**Terminal 1:**
```
2024-10-26 18:17:00,123 - src.api.agents - ERROR - Failed to deploy agent: relation "agent_deployments" does not exist
INFO:     127.0.0.1:54329 - "POST /api/v1/agents/deploy HTTP/1.1" 500 Internal Server Error
```

**Terminal 2:**
```
Deployment failed with status 500
{"detail":"Deployment failed: relation \"agent_deployments\" does not exist"}
```

## With DEBUG=true

When `DEBUG=true` in `.env`, you'll see additional debug logs:

```
2024-10-26 18:12:34,100 - src.database - DEBUG - Executing query: INSERT INTO agent_deployments...
2024-10-26 18:12:34,110 - src.database - DEBUG - Query parameters: ['550e8400-e29b-41d4-a716-446655440000', 'simple-calculator', 'RUNNING', ...]
2024-10-26 18:12:34,120 - src.database - DEBUG - Query completed in 10ms
2024-10-26 18:12:34,123 - src.api.agents - INFO - Deployed agent simple-calculator with deployment_id 550e8400-e29b-41d4-a716-446655440000
```

## Key Logging Points

### 1. `src/api/agents.py`
- **Line 55**: Deployment success log
- **Line 67**: Deployment error log
- **Line 125**: Invocation log (all statuses)
- **Line 140**: Invocation error log
- **Line 182**: Status check error log
- **Line 203**: Agent deletion log
- **Line 207**: Deletion error log

### 2. `src/agents/executor.py`
- **Line 76**: Timeout warning
- **Line 80**: Execution error log

### 3. `src/database.py`
Connection and query logs (if logging enabled)

## Verifying Logs Work

Check these things:

1. ✅ **Timestamp present**: Each log has a timestamp
2. ✅ **Module name**: Shows which file logged (e.g., `src.api.agents`)
3. ✅ **Level**: INFO, ERROR, WARNING, DEBUG
4. ✅ **Message**: Clear, actionable information
5. ✅ **Context**: Includes IDs (agent_id, deployment_id, invocation_id)
6. ✅ **Status**: Shows operation result (SUCCESS, ERROR, TIMEOUT)

## Next: Enhance Logging

Add more context to logs:

```python
# In src/api/agents.py
logger.info(
    f"Deployed agent {request.agent_id} with deployment_id {deployment_id}",
    extra={
        "agent_id": request.agent_id,
        "deployment_id": deployment_id,
        "code_hash": code_hash,
        "memory_limit": request.max_memory,
        "cpu_limit": request.max_cpu
    }
)
```

For structured JSON logs:
```json
{
  "timestamp": "2024-10-26T18:12:34.123456Z",
  "level": "INFO",
  "logger": "src.api.agents",
  "message": "Deployed agent simple-calculator with deployment_id 550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "simple-calculator",
  "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
  "code_hash": 1234567890,
  "memory_limit": "256m",
  "cpu_limit": "0.25"
}
```
