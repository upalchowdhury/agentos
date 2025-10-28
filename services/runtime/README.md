# Agent Runtime Service

A production-grade FastAPI service for deploying and executing AI agents in the Agent Economy OS.

## Features

- **Model A (Runtime Build Pipeline)**: Upload Python artifacts, build sandboxed images, and auto-provision execution endpoints.
- **Model B (External Registry)**: Register 3rd-party agents (OpenAI, Salesforce, MCP, custom HTTP) with centralized rate limits and health tracking.
- **Secured Execution**: Hardened executor with restricted built-ins, deterministic cost metering, and configurable timeouts.
- **Governance Hooks**: Optional OPA integration for RBAC/obligations and audit-ready invocation logging.
- **Persistent State**: PostgreSQL schema for agents, versions, invocations, and aggregated cost metrics.
- **Observability**: Health endpoint plus structured logs, with placeholders for metrics and tracing exporters.

## Architecture

```
services/runtime/
├── src/
│   ├── main.py           # FastAPI application with lifespan management
│   ├── config.py         # Settings and configuration
│   ├── models.py         # Legacy Pydantic models and enums
│   ├── models_v2.py      # Unified Model A & B schemas
│   ├── database.py       # Async database connection pool
│   ├── agents/
│   │   ├── executor.py   # Agent code execution engine
│   │   ├── builder.py    # Artifact handling and deployment wiring
│   │   ├── proxy.py      # External agent proxy integration
│   │   ├── deployer.py   # Container deployment (TODO)
│   │   └── monitor.py    # Metrics collection (TODO)
│   └── api/
│       ├── agents.py     # Agent deployment and invocation endpoints
│       ├── agents_v2.py  # Model A/B APIs with registry support
│       └── health.py     # Health check endpoints
├── tests/
│   ├── conftest.py       # Test helpers (path setup)
│   ├── test_executor.py  # Executor unit tests
│   ├── test_deployer.py  # Deployer module tests
│   ├── test_api.py       # Import smoke tests
│   └── integration/      # (Skipped) requires live service + DB
├── artifacts/            # Local artifact cache (gitignored)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container image definition
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
   psql -h localhost -U agentos -d agentos -f ../../infra/migrations/005_enhanced_runtime_schema.sql
   ```

6. **Start the service:**
   ```bash
   python -m src.main  # or `uvicorn services.runtime.src.main:app --reload`
   ```

7. **Access the API:**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Root: http://localhost:8000/

## API Endpoints

### Model A (Code Upload)

- **POST `/v1/agents/modelA`** – Create an agent shell, returns upload URL and deployment ID.
- **PUT `/v1/agents/{agent_id}/artifact`** – Upload a Python file/zip, triggers build and runtime deployment.
- **GET `/v1/agents/{agent_id}/build`** – Retrieve build status, logs, and image reference.

Sample deploy payload:

```json
{
  "name": "my-analysis-agent",
  "runtime": "python3.11",
  "requirements": ["pandas"],
  "env": {"OPENAI_API_KEY": "sk-..."},
  "resources": {"cpu": "500m", "mem": "1Gi"}
}
```

### Model B (External Registry)

- **POST `/v1/agents/modelB`** – Register an external endpoint with auth and rate limits.
- **POST `/v1/agents/{agent_id}/invoke`** – Unified invocation (proxy for Model B, runtime for Model A).
- **GET `/v1/agents/{agent_id}`** – Inspect agent metadata, status, and cost.
- **DELETE `/v1/agents/{agent_id}`** – Soft-delete/terminate an agent (all models).

Example registry payload:

```json
{
  "name": "external-openai-agent",
  "endpoint_url": "https://api.openai.com/v1/assistants",
  "auth": {"type": "bearer", "value": "sk-test"},
  "rate_limit": {"rps": 10, "burst": 20}
}
```

### Legacy Runtime (v1)

- **POST `/api/v1/agents/deploy`** – Inline code deploy (backwards compatibility).
- **POST `/api/v1/agents/invoke`** – Invoke legacy agents.
- **GET `/api/v1/agents/{agent_id}/status`** – Deployment summary.
- **DELETE `/api/v1/agents/{agent_id}`** – Terminate latest deployment.
- **GET `/health`** – Health probe.

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
- `OPA_URL`: Optional Open Policy Agent endpoint for RBAC decisions

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
