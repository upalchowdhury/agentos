# Agent Runtime Service

A production-grade FastAPI service for deploying and executing AI agents in the Agent Economy OS.

## Features

- **Agent Deployment**: Deploy agents with custom code and resource limits
- **Agent Invocation**: Execute deployed agents with input data and timeouts
- **Status Monitoring**: Track agent deployments, invocations, and metrics
- **Safe Execution**: Restricted Python environment for secure code execution
- **Cost Tracking**: Track execution time and estimated costs per invocation
- **Database Persistence**: PostgreSQL with async connection pooling
- **Health Checks**: Built-in health endpoints for monitoring
- **RESTful API**: OpenAPI/Swagger documentation included

## Architecture

```
services/runtime/
├── src/
│   ├── main.py           # FastAPI application with lifespan management
│   ├── config.py         # Settings and configuration
│   ├── models.py         # Pydantic models and enums
│   ├── database.py       # Async database connection pool
│   ├── agents/
│   │   ├── executor.py   # Agent code execution engine
│   │   ├── deployer.py   # Container deployment (TODO)
│   │   └── monitor.py    # Metrics collection (TODO)
│   └── api/
│       ├── agents.py     # Agent deployment and invocation endpoints
│       └── health.py     # Health check endpoints
├── tests/
│   ├── test_executor.py  # Executor unit tests
│   ├── test_deployer.py  # Deployer module tests
│   └── test_api.py       # API integration tests
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container image definition
└── .env.example         # Environment variables template
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis (optional, for future caching)

### Local Development

1. **Clone and navigate to the service:**
   ```bash
   cd services/runtime
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run database migrations:**
   ```bash
   # Ensure PostgreSQL is running, then:
   psql -h localhost -U agentos -d agentos -f ../../infra/migrations/004_runtime_schema.sql
   ```

6. **Start the service:**
   ```bash
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API:**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Root: http://localhost:8000/

## API Endpoints

### Deployment

**POST /api/v1/agents/deploy**

Deploy a new agent with custom code.

```json
{
  "agent_id": "my-agent",
  "code": "result = input_data['x'] + input_data['y']",
  "requirements": [],
  "environment": null,
  "max_memory": "512m",
  "max_cpu": "0.5"
}
```

### Invocation

**POST /api/v1/agents/invoke**

Execute a deployed agent.

```json
{
  "agent_id": "my-agent",
  "input_data": {"x": 10, "y": 20},
  "timeout": 30
}
```

### Status

**GET /api/v1/agents/{agent_id}/status**

Get agent deployment and invocation statistics.

### Deletion

**DELETE /api/v1/agents/{agent_id}**

Terminate an agent deployment.

### Health

**GET /health**

Check service health (database connectivity, executor status).

## Testing

### Run Unit Tests

```bash
cd services/runtime
pytest -v
```

### Run Specific Test Files

```bash
pytest tests/test_executor.py -v
pytest tests/test_deployer.py -v
pytest tests/test_api.py -v
```

### Test Scripts

Manual API testing scripts are provided:

```bash
# Deploy an agent
python test_deploy.py

# Invoke the deployed agent
python test_invoke.py

# Check agent status
python test_status.py

# End-to-end customer support agent test
python test_e2e.py
```

## Docker

### Build Image

```bash
cd services/runtime
docker build -t agentos/runtime:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=agentos \
  -e POSTGRES_USER=agentos \
  -e POSTGRES_PASSWORD=yourpassword \
  agentos/runtime:latest
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster running
- `agentos` namespace created
- PostgreSQL deployed in cluster
- Secrets configured (`agentos-secrets`)

### Deploy

```bash
kubectl apply -f ../../k8s/08-runtime.yaml
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n agentos | grep runtime

# Check logs
kubectl logs -n agentos -l app=runtime --tail=100 -f

# Port forward for local testing
kubectl port-forward -n agentos svc/runtime 8000:8000
```

### Apply Database Migration

```bash
# Port forward PostgreSQL
kubectl port-forward -n agentos svc/postgres 5432:5432

# Run migration
psql -h localhost -U agentos -d agentos -f ../../infra/migrations/004_runtime_schema.sql
```

## Configuration

All configuration is managed via environment variables. See `.env.example` for available options.

Key settings:
- `POSTGRES_*`: Database connection parameters
- `REDIS_*`: Redis connection (future use)
- `DEFAULT_MEMORY_LIMIT`: Default memory limit for agents
- `DEFAULT_CPU_LIMIT`: Default CPU limit for agents
- `MAX_EXECUTION_TIME`: Maximum execution timeout (seconds)

## Security

- **Safe Execution Environment**: Agent code runs in a restricted Python environment with no access to file system, network, or imports
- **Input Validation**: All API inputs validated with Pydantic
- **Timeout Protection**: Execution timeouts prevent runaway code
- **Resource Limits**: CPU and memory limits enforced (Docker deployment)
- **Database Prepared Statements**: Protection against SQL injection

## Performance

- Async connection pooling (5-20 connections)
- Query timeouts (60 seconds)
- Thread pool execution for synchronous code
- Efficient database indexing

## Monitoring

- Health check endpoint with database connectivity test
- Structured logging with timestamps and levels
- Metrics tables for resource usage tracking (future implementation)

## Development Roadmap

### Current (MVP)
- [x] Agent deployment and invocation
- [x] Safe code execution
- [x] Database persistence
- [x] Health checks
- [x] Unit tests

### Future Enhancements
- [ ] Docker container deployment per agent
- [ ] Real-time metrics collection
- [ ] Redis caching for hot paths
- [ ] Rate limiting
- [ ] Agent versioning
- [ ] Distributed tracing
- [ ] Prometheus metrics export

## Troubleshooting

### Database Connection Errors

```bash
# Check PostgreSQL is running
psql -h localhost -U agentos -d agentos -c "SELECT 1"

# Verify migrations applied
psql -h localhost -U agentos -d agentos -c "\dt"
```

### Import Errors in Tests

```bash
# Install in development mode
pip install -e .

# Or run from correct directory
cd /path/to/agentos
export PYTHONPATH=/path/to/agentos:$PYTHONPATH
pytest services/runtime/tests/ -v
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

## Contributing

1. Follow production-grade coding standards
2. Add tests for all new functionality
3. Update documentation for API changes
4. Ensure all tests pass before committing

## License

Part of Agent Economy OS. See LICENSE in repository root.

---

## Verification Checklist

**Day 1-2: Foundation**
- [x] Directory structure created
- [x] Requirements and dependencies defined
- [x] Configuration with environment variables
- [x] Pydantic models with validation
- [x] Database connection pool with asyncpg
- [x] SQL migration script

**Day 3-4: Core Logic**
- [x] Agent executor with safe environment
- [x] Executor unit tests (6 test cases)
- [x] API endpoints (deploy, invoke, status, delete)
- [x] Health check endpoint
- [x] Main FastAPI app with lifespan

**Day 5: Infrastructure**
- [x] Dockerfile with multi-stage build
- [x] Kubernetes deployment manifest
- [x] README with comprehensive documentation

**Day 6-7: Integration & Testing**
- [x] Test scripts (deploy, invoke, status, e2e)
- [x] Placeholder modules (deployer, monitor)
- [x] Smoke tests for imports
- [x] All files created and tested

**Status: COMPLETE**
