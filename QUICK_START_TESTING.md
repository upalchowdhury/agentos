# Quick Start: Testing Agent Deployment with Logging

**Goal**: Deploy a simple agent and verify that logging works end-to-end.

## Option 1: Automated Quick Test (Recommended)

Run the automated setup script:

```bash
cd services/runtime
./quick_test.sh
```

This will:
- Check PostgreSQL is running
- Verify/create database schema
- Create `.env` configuration
- Install Python dependencies

Then follow the printed instructions to start the server and run tests.

## Option 2: Manual Step-by-Step

### Step 1: Start PostgreSQL

```bash
# Using Docker
docker run --name agentos-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agentos \
  -p 5432:5432 \
  -d postgres:16-alpine

# Wait for it to start
sleep 5
```

### Step 2: Create Database Schema

```bash
cd /Users/upalc/AgentOS/agentos

# Apply migration
PGPASSWORD=postgres psql -h localhost -U postgres -d agentos \
  -f infra/migrations/004_runtime_schema.sql
```

### Step 3: Configure Runtime Service

```bash
cd services/runtime

# Create .env file
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

### Step 4: Install Dependencies

```bash
# Still in services/runtime/
pip install -r requirements.txt
```

### Step 5: Start Runtime Service

Open Terminal 1:

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python -m src.main
```

**Expected Output:**
```
2024-10-26 18:10:00 - src.config - INFO - ...
2024-10-26 18:10:00 - src.main - INFO - Starting Runtime service
2024-10-26 18:10:00 - src.database - INFO - Connecting to database...
2024-10-26 18:10:00 - src.main - INFO - Runtime service ready
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 6: Run Agent Test

Open Terminal 2:

```bash
cd /Users/upalc/AgentOS/agentos/services/runtime
python test_simple_agent.py
```

**Expected Output:**
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

... (more tests)

============================================================
CHECKING AGENT STATUS
============================================================
Agent ID: simple-calculator
Status: RUNNING
Deployed At: 2024-10-26T18:12:34.567890
Total Invocations: 4
Last Invocation: 2024-10-26T18:12:35.123456

============================================================
TEST COMPLETED
============================================================
```

### Step 7: Verify Logs in Terminal 1

In your server terminal (Terminal 1), you should see:

```
INFO:     127.0.0.1:54321 - "POST /api/v1/agents/deploy HTTP/1.1" 200 OK
2024-10-26 18:12:34 - src.api.agents - INFO - Deployed agent simple-calculator with deployment_id 550e8400-e29b-41d4-a716-446655440000

INFO:     127.0.0.1:54322 - "POST /api/v1/agents/invoke HTTP/1.1" 200 OK
2024-10-26 18:12:35 - src.api.agents - INFO - Invoked agent simple-calculator, invocation_id 550e8400-e29b-41d4-a716-446655440001, status SUCCESS

... (more log entries for each invocation)

INFO:     127.0.0.1:54323 - "GET /api/v1/agents/simple-calculator/status HTTP/1.1" 200 OK
```

## What's Happening?

### 1. **Deployment** (`POST /api/v1/agents/deploy`)

The test sends agent code to the runtime service. The service:
- Stores the code in `agent_deployments` table
- Returns a deployment ID
- **Logs**: `Deployed agent {agent_id} with deployment_id {uuid}`

### 2. **Invocation** (`POST /api/v1/agents/invoke`)

For each test case, the service:
- Retrieves the agent code from the database
- Executes it in a sandboxed environment with input data
- Records the result in `agent_invocations` table
- **Logs**: `Invoked agent {agent_id}, invocation_id {uuid}, status {status}`

### 3. **Status Check** (`GET /api/v1/agents/{agent_id}/status`)

Queries deployment and invocation records to show:
- Current agent status
- Number of invocations
- Last invocation time

## Key Files to Understand

1. **`src/api/agents.py`** - API endpoints with logging
   - Line 55: Deployment logging
   - Line 125: Invocation logging

2. **`src/agents/executor.py`** - Agent execution logic
   - Sandboxed Python execution
   - Timeout handling
   - Error logging (lines 76, 80)

3. **`src/config.py`** - Logging configuration
   - Line 58-61: Basic logging setup

4. **`test_simple_agent.py`** - Test script
   - Deploys calculator agent
   - Tests multiple operations
   - Shows expected output

## Next Steps

### Add More Logging

Edit `src/agents/executor.py` to add execution logs:

```python
async def execute(self, agent_id: str, code: str, input_data: dict, timeout: int = 30):
    logger.info(f"Starting execution for agent {agent_id}")
    
    # ... existing code ...
    
    try:
        logger.debug(f"Executing code for {agent_id} with input: {input_data}")
        output = await asyncio.wait_for(...)
        logger.info(f"Execution succeeded for {agent_id} in {execution_time_ms}ms")
    except Exception as e:
        logger.error(f"Execution failed for {agent_id}: {e}", exc_info=True)
```

### Test Different Agents

Create more test files:

```python
# test_sentiment_agent.py
agent_code = """
text = input_data['text'].lower()
if 'love' in text or 'great' in text:
    sentiment = 'positive'
elif 'hate' in text or 'bad' in text:
    sentiment = 'negative'
else:
    sentiment = 'neutral'
    
result = {'text': input_data['text'], 'sentiment': sentiment}
"""
```

### Structured Logging

For production, implement JSON logging (see `AGENT_TESTING_GUIDE.md`).

### Monitoring

- Check database for stored invocations: `SELECT * FROM agent_invocations ORDER BY invoked_at DESC LIMIT 10;`
- View agent statistics: `SELECT * FROM agent_stats;`

## Troubleshooting

### "Connection refused" error
- Check runtime service is running: `lsof -i :8000`
- Verify PORT in `.env` matches

### "No running deployment found"
- Deployment failed or agent_id mismatch
- Check: `SELECT * FROM agent_deployments;`

### Agent execution errors
- Check syntax: agent code must set `result` variable
- View error in test output or server logs

### No logs appearing
- Verify `DEBUG=true` in `.env`
- Check logging level in `src/config.py`
- Restart server after config changes

## Summary

You've successfully:
1. ✅ Set up the runtime service
2. ✅ Deployed a simple agent
3. ✅ Executed the agent with test data
4. ✅ Verified logging at each step

The logging system is working! You can now:
- Create more complex agents
- Add additional logging points
- Integrate with observability tools (OpenTelemetry, Grafana)
- Deploy to production with structured logging
