# Runtime Service Deployment Guide

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Docker (for containerized deployment)
- Kubernetes cluster (for K8s deployment)

### Local Development Setup

1. **Install Dependencies**
```bash
cd services/runtime
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run Database Migration**
```bash
# Connect to your PostgreSQL instance
psql -h localhost -U agentos -d agentos -f ../../infra/migrations/004_runtime_schema.sql
```

4. **Start the Service**
```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Verify Installation**
```bash
# Check health endpoint
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

### Testing

**Run All Tests**
```bash
cd services/runtime
pytest -v
```

**Run Specific Test Suites**
```bash
pytest tests/test_executor.py -v
pytest tests/test_api.py -v
pytest tests/test_deployer.py -v
```

**Manual API Testing**
```bash
# Deploy an agent
python test_deploy.py

# Invoke the agent
python test_invoke.py

# Check agent status
python test_status.py

# Run end-to-end test
python test_e2e.py
```

### Docker Deployment

1. **Build Image**
```bash
cd services/runtime
docker build -t agentos/runtime:latest .
```

2. **Run Container**
```bash
docker run -d \
  --name runtime-service \
  -p 8000:8000 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=agentos \
  -e POSTGRES_USER=agentos \
  -e POSTGRES_PASSWORD=yourpassword \
  agentos/runtime:latest
```

3. **View Logs**
```bash
docker logs -f runtime-service
```

### Kubernetes Deployment

1. **Prerequisites**
```bash
# Ensure namespace exists
kubectl create namespace agentos

# Create secrets (if not already created)
kubectl create secret generic agentos-secrets \
  --from-literal=POSTGRES_USER=agentos \
  --from-literal=POSTGRES_PASSWORD=yourpassword \
  -n agentos
```

2. **Apply Migration**
```bash
# Port forward to PostgreSQL
kubectl port-forward -n agentos svc/postgres 5432:5432

# Run migration in another terminal
psql -h localhost -U agentos -d agentos -f ../../infra/migrations/004_runtime_schema.sql
```

3. **Deploy Service**
```bash
kubectl apply -f ../../k8s/08-runtime.yaml
```

4. **Verify Deployment**
```bash
# Check pod status
kubectl get pods -n agentos -l app=runtime

# Check service
kubectl get svc -n agentos runtime

# View logs
kubectl logs -n agentos -l app=runtime --tail=100 -f

# Check health
kubectl port-forward -n agentos svc/runtime 8000:8000
curl http://localhost:8000/health
```

### Gateway Integration

The Runtime Service is integrated with the Gateway service. Ensure the Gateway is configured with:

```bash
# Gateway environment variable
RUNTIME_SERVICE_URL=http://runtime:8000
```

Gateway routes proxy to Runtime Service:
- `POST /api/v1/agents/deploy` → Runtime Service
- `POST /api/v1/agents/invoke` → Runtime Service
- `GET /api/v1/agents/{id}/status` → Runtime Service
- `DELETE /api/v1/agents/{id}` → Runtime Service

### Web UI Integration

The Web UI includes a "Deploy Agent" page at `/deploy` that allows users to:
- Enter Agent ID
- Provide agent code
- Configure resource limits (memory, CPU)
- Deploy agents via the Gateway

Access the Deploy Agent page after starting the Web UI:
```bash
cd services/web-ui
npm install
npm run dev
# Navigate to http://localhost:5173/deploy
```

## API Usage Examples

### Deploy an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math-agent",
    "code": "result = input_data[\"x\"] + input_data[\"y\"]",
    "requirements": [],
    "environment": null,
    "max_memory": "512m",
    "max_cpu": "0.5"
  }'
```

### Invoke an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math-agent",
    "input_data": {"x": 10, "y": 20},
    "timeout": 30
  }'
```

### Get Agent Status

```bash
curl http://localhost:8000/api/v1/agents/math-agent/status
```

### Delete an Agent

```bash
curl -X DELETE http://localhost:8000/api/v1/agents/math-agent
```

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

Response includes:
- Overall status (healthy/unhealthy)
- Database connectivity check
- Executor availability check

### Logs

Structured logs include:
- Timestamp
- Log level (INFO, WARNING, ERROR)
- Component name
- Message with context

### Metrics (Future)

Planned metrics exposure:
- Prometheus metrics endpoint
- Agent invocation counts
- Execution time histograms
- Error rates
- Resource usage

## Troubleshooting

### Database Connection Issues

```bash
# Test database connectivity
psql -h localhost -U agentos -d agentos -c "SELECT 1"

# Verify tables exist
psql -h localhost -U agentos -d agentos -c "\dt"

# Check migration was applied
psql -h localhost -U agentos -d agentos -c "SELECT * FROM agent_deployments LIMIT 1"
```

### Service Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Verify all dependencies installed
pip list | grep -E "(fastapi|uvicorn|asyncpg|pydantic)"

# Check for port conflicts
lsof -i :8000

# View detailed error logs
python -m uvicorn src.main:app --reload --log-level debug
```

### Tests Failing

```bash
# Install in development mode
cd services/runtime
pip install -e .

# Set PYTHONPATH
export PYTHONPATH=/Users/upalc/AgentOS/agentos:$PYTHONPATH

# Run tests with verbose output
pytest -v -s
```

### Agent Execution Timeouts

- Default timeout is 30 seconds (configurable via `MAX_EXECUTION_TIME`)
- Adjust timeout in invocation request: `"timeout": 60`
- Check agent code for infinite loops or expensive operations

### Import Errors in Agent Code

Agent code runs in a restricted environment with no import capabilities. Use only built-in functions:
- Arithmetic: `+`, `-`, `*`, `/`, `**`, `%`
- Built-ins: `len`, `str`, `int`, `float`, `dict`, `list`, etc.
- Control flow: `if`, `for`, `while`
- String operations: `.upper()`, `.lower()`, `.split()`, etc.

## Security Notes

- Agent code runs in sandboxed environment
- No file system access
- No network access
- No import capabilities
- Input validation via Pydantic models
- SQL injection protection via parameterized queries
- Resource limits enforced (memory, CPU, timeout)

## Performance Tips

- Database connection pool: 5-20 connections
- Adjust pool size based on load: `min_size=5`, `max_size=20`
- Use indexes for frequent queries (already configured)
- Monitor execution times and adjust timeouts
- Consider caching for frequently accessed data (future enhancement)

## Next Steps

1. **Production Deployment**: Configure production database credentials and resource limits
2. **Monitoring Setup**: Implement Prometheus metrics and alerting
3. **Container Deployment**: Enable Docker-per-agent deployment via deployer module
4. **Metrics Collection**: Implement real-time metrics via monitor module
5. **Rate Limiting**: Add rate limiting per agent/user
6. **Authentication**: Integrate with identity service for auth tokens

## Support

For issues or questions:
1. Check logs: `kubectl logs -n agentos -l app=runtime`
2. Review API docs: `http://localhost:8000/docs`
3. Verify health: `http://localhost:8000/health`
4. Run test suite: `pytest -v`

## Architecture Summary

```
Runtime Service
├── FastAPI Application
│   ├── Lifespan: DB connection management
│   ├── CORS: Allow all origins (configure for production)
│   └── Routes: /api/v1/agents/*, /health, /
├── Database Layer
│   ├── AsyncPG connection pool
│   ├── Transaction support
│   └── Error handling with reconnection
├── Agent Executor
│   ├── Safe execution environment
│   ├── Timeout protection
│   ├── Cost estimation
│   └── Thread pool for sync code
├── API Endpoints
│   ├── Deploy: POST /api/v1/agents/deploy
│   ├── Invoke: POST /api/v1/agents/invoke
│   ├── Status: GET /api/v1/agents/{id}/status
│   └── Delete: DELETE /api/v1/agents/{id}
└── Testing
    ├── Unit tests: test_executor.py
    ├── Integration tests: test_api.py
    └── E2E tests: test_e2e.py
```

## Database Schema

**Tables:**
- `agent_deployments`: Agent deployment records with code and metadata
- `agent_invocations`: Invocation history with results and costs
- `agent_metrics`: Time-series metrics for resource usage

**Indexes:**
- `idx_deployments_agent`: Fast agent lookup
- `idx_deployments_status`: Status filtering
- `idx_invocations_agent_time`: Agent invocation history
- `idx_invocations_deployment`: Deployment linkage
- `idx_metrics_time`: Time-series queries

**View:**
- `agent_stats`: Aggregated statistics per agent

## Completed Implementation Checklist

- [x] Python FastAPI service with async support
- [x] PostgreSQL database integration with asyncpg
- [x] Safe agent execution environment
- [x] API endpoints (deploy, invoke, status, delete)
- [x] Health check endpoint
- [x] Pydantic models with validation
- [x] Database migration SQL
- [x] Unit tests (executor, deployer, api)
- [x] Integration test scripts
- [x] End-to-end test
- [x] Dockerfile for containerization
- [x] Kubernetes deployment manifest
- [x] Gateway integration (Go proxy routes)
- [x] Web UI integration (React DeployAgent page)
- [x] Comprehensive documentation
- [x] README with setup instructions
- [x] Deployment guide

**Status: PRODUCTION-READY MVP**
