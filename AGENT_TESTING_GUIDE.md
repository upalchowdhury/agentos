# Agent Testing Guide - Deploy & Verify Logging

This guide walks you through deploying a test agent and verifying that the logging system works correctly.

## Prerequisites

1. **PostgreSQL running** (local or Docker)
2. **Python 3.11+** installed
3. **Runtime service dependencies** installed

## Quick Start

### 1. Setup Database

First, ensure PostgreSQL is running with the required schema:

```bash
# If using local postgres
psql -U postgres -d agentos -f infra/migrations/004_runtime_schema.sql

# Or with Docker
docker run --name agentos-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=agentos -p 5432:5432 -d postgres:16-alpine
sleep 5
docker exec -i agentos-postgres psql -U postgres -d agentos < infra/migrations/004_runtime_schema.sql
```

### 2. Configure Environment

Create a `.env` file in `services/runtime/`:

```bash
# services/runtime/.env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DEBUG=true
```

### 3. Install Dependencies

```bash
cd services/runtime
pip install -r requirements.txt
```

### 4. Start the Runtime Service

In one terminal:

```bash
cd services/runtime
python -m src.main
```

You should see logs like:
```
2024-10-26 18:10:00 - src.main - INFO - Starting Runtime service
2024-10-26 18:10:00 - src.database - INFO - Connecting to database...
2024-10-26 18:10:00 - src.main - INFO - Runtime service ready
```

### 5. Run the Test Agent

In another terminal:

```bash
cd services/runtime
python test_simple_agent.py
```

## What to Look For

### Server Logs (Terminal 1)

Watch for these log entries when you run the test:

```
INFO - Deployed agent simple-calculator with deployment_id <uuid>
INFO - Invoked agent simple-calculator, invocation_id <uuid>, status SUCCESS
```

### Test Output (Terminal 2)

You should see:

```
========================================
DEPLOYING SIMPLE CALCULATOR AGENT
========================================
Deploy Status: 200
Deployment ID: <uuid>
Status: RUNNING

========================================
TESTING CALCULATIONS
========================================
[1] Testing: Add 5 + 3
    Status: SUCCESS
    Output: {'operation': 'add', 'result': 8}
    Execution Time: <X>ms

[2] Testing: Multiply 4 * 7
    Status: SUCCESS
    Output: {'operation': 'multiply', 'result': 28}
    Execution Time: <X>ms

========================================
CHECKING AGENT STATUS
========================================
Agent ID: simple-calculator
Status: RUNNING
Total Invocations: 2
```

## Key Logging Points

The runtime service logs at these important points:

1. **Deployment** (`src/api/agents.py:55`):
   ```python
   logger.info(f"Deployed agent {request.agent_id} with deployment_id {deployment_id}")
   ```

2. **Invocation** (`src/api/agents.py:125`):
   ```python
   logger.info(f"Invoked agent {request.agent_id}, invocation_id {invocation_id}, status {execution_result['status']}")
   ```

3. **Errors** (various locations):
   ```python
   logger.error(f"Failed to deploy agent: {e}")
   logger.error(f"Failed to invoke agent: {e}")
   ```

## Troubleshooting

### No logs appearing?

1. Check `DEBUG=true` is set in `.env`
2. Verify logging is configured in `src/config.py`:
   ```python
   logging.basicConfig(
       level=logging.INFO if not settings.DEBUG else logging.DEBUG,
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
   )
   ```

### Database connection errors?

```bash
# Test connection
psql -U postgres -d agentos -c "SELECT 1"

# Check tables exist
psql -U postgres -d agentos -c "\dt"
```

### Agent execution fails?

The agent executor currently stores code but doesn't execute in containers. Check:
- Code syntax is valid Python
- No external dependencies required
- Check `src/agents/executor.py` for execution logic

## Advanced: Structured Logging

To enable structured JSON logging (production-ready):

Edit `src/config.py`:

```python
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "runtime-service"
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
```

## Next Steps

1. **Add more log points** in `src/agents/executor.py`
2. **Integrate OpenTelemetry** for distributed tracing
3. **Export logs** to ClickHouse or Elasticsearch
4. **Add log aggregation** with Grafana Loki

## Reference Files

- API endpoints: `services/runtime/src/api/agents.py`
- Configuration: `services/runtime/src/config.py`
- Database schema: `infra/migrations/004_runtime_schema.sql`
- Existing tests: `services/runtime/test_e2e.py`
