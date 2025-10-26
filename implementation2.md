You are an expert repo refactorer + code generator. Apply the following plan EXACTLY, step-by-step, to the project already open in this workspace.

# ===============================
# Agent Economy OS — Runtime Service MVP (One-Shot Build)
# Goal: Ship a working Runtime Service (FastAPI + asyncpg) with tests, Docker, K8s, and UI/Gateway integration.
# Constraints: Production-grade structure, type hints, error handling, clear logs. Follow instructions precisely.
# ===============================

## 0) Preflight
- Assume repo root is `agentos/`.
- If a path already exists, update/overwrite files as instructed (do not duplicate).
- Use Python 3.11 semantics.
- Keep code minimal yet robust; no dead code; tight lint-friendly style.

## 1) Create Directory Structure (empty files first, then we'll fill)
Create the following under repo root:

agentos/
├── services/
│   ├── identity/          # (exists, leave as-is)
│   ├── gateway/           # (exists, we'll edit later)
│   ├── web-ui/            # (exists, we'll edit later)
│   └── runtime/
│       ├── src/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── models.py
│       │   ├── database.py
│       │   ├── agents/
│       │   │   ├── __init__.py
│       │   │   ├── executor.py
│       │   │   ├── deployer.py
│       │   │   └── monitor.py
│       │   └── api/
│       │       ├── __init__.py
│       │       ├── agents.py
│       │       └── health.py
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── test_executor.py
│       │   ├── test_deployer.py
│       │   └── test_api.py
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── .env.example
│       └── README.md
├── infra/
│   └── migrations/
│       └── 004_runtime_schema.sql
└── k8s/
    └── 08-runtime.yaml

## 2) Populate files

### 2.1 services/runtime/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
docker==7.0.0
psycopg2-binary==2.9.9
asyncpg==0.29.0
httpx==0.25.2
redis==5.0.1
pytest==7.4.3
pytest-asyncio==0.21.1

### 2.2 services/runtime/.env.example
# Service
SERVICE_NAME=runtime-service
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agentos
POSTGRES_USER=agentos
POSTGRES_PASSWORD=changeme

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_NETWORK=agentos-network

# Agent Execution
DEFAULT_MEMORY_LIMIT=512m
DEFAULT_CPU_LIMIT=0.5
MAX_EXECUTION_TIME=30

# Services
IDENTITY_SERVICE_URL=http://identity:3000
GATEWAY_SERVICE_URL=http://gateway:8080

### 2.3 services/runtime/src/config.py
- Implement a `Settings` class using `BaseSettings` from `pydantic_settings`.
- Include all vars from `.env.example` with proper types (int/str/bool).
- Add computed properties:
  - `database_url: str` → `postgresql://{user}:{password}@{host}:{port}/{db}`
  - `redis_url: str` → `redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}`
- Inner Config: `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`
- Instantiate `settings = Settings()` at bottom.
- Add minimal logging setup (INFO level) readable by uvicorn.

### 2.4 services/runtime/src/models.py
Define:
- Enums: `AgentStatus` (DEPLOYING, RUNNING, STOPPED, FAILED, TERMINATED), `InvocationStatus` (SUCCESS, ERROR, TIMEOUT).
- Request models:
  - `DeploymentRequest(agent_id:str, code:str, requirements:list[str], environment:dict[str,str]|None, max_memory:str, max_cpu:str)`
  - `InvocationRequest(agent_id:str, input_data:dict, timeout:int)`
- Response models:
  - `DeploymentResponse(deployment_id:str, agent_id:str, status:AgentStatus, container_id:str|None, endpoint:str|None, deployed_at:datetime, message:str|None)`
  - `InvocationResponse(invocation_id:str, agent_id:str, status:InvocationStatus, output:Any|None, error:str|None, execution_time_ms:int, cost_cents:int, invoked_at:datetime)`
  - `AgentStatusResponse(agent_id:str, status:AgentStatus, container_id:str|None, deployed_at:datetime|None, last_invocation:datetime|None, invocation_count:int, cpu_percent:float|None, memory_mb:int|None, uptime_seconds:int|None)`
  - `HealthResponse(status:str, service:str, timestamp:datetime, checks:dict[str,bool])`
- Validators/constraints:
  - `code` length: 10–50000 chars
  - `requirements` max 50 items
  - `timeout` 1–300 seconds
- Use `Field` with descriptions.

### 2.5 services/runtime/src/database.py
Create async `Database` using `asyncpg`:
- Pool: `min_size=5`, `max_size=20`
- Methods:
  - `connect()`, `disconnect()`
  - `@asynccontextmanager transaction()`
  - `execute(query,*args)`, `fetch(query,*args)`, `fetchrow(query,*args)`
- Use DSN from `settings.database_url`.
- Robust error logging and reconnection handling.
- Export `db = Database()`.

### 2.6 infra/migrations/004_runtime_schema.sql
Create (IF NOT EXISTS) tables:

1) agent_deployments
- id UUID PK default gen_random_uuid() if available; otherwise use uuid_generate_v4(); if neither, leave for app to supply
- agent_did VARCHAR(255) NOT NULL
- status VARCHAR(50) CHECK (status IN ('DEPLOYING','RUNNING','STOPPED','FAILED','TERMINATED'))
- container_id VARCHAR(255) NULL
- code TEXT
- code_hash BIGINT
- resource_limits JSONB
- deployed_at TIMESTAMPTZ DEFAULT NOW()
- stopped_at TIMESTAMPTZ NULL
- metadata JSONB

2) agent_invocations
- id UUID PK
- agent_did VARCHAR(255)
- deployment_id UUID REFERENCES agent_deployments(id) ON DELETE CASCADE
- input_hash VARCHAR(64) NULL
- output_hash VARCHAR(64) NULL
- status VARCHAR(50) CHECK (status IN ('SUCCESS','ERROR','TIMEOUT'))
- execution_time_ms INTEGER
- cost_cents INTEGER DEFAULT 0
- invoked_at TIMESTAMPTZ DEFAULT NOW()
- error_message TEXT NULL

3) agent_metrics
- agent_did VARCHAR(255)
- timestamp TIMESTAMPTZ
- cpu_percent FLOAT
- memory_mb INTEGER
- network_rx_bytes BIGINT
- network_tx_bytes BIGINT
- active_connections INTEGER
- PRIMARY KEY (agent_did, timestamp)

Indexes:
- idx_deployments_agent ON agent_deployments(agent_did)
- idx_deployments_status ON agent_deployments(status)
- idx_invocations_agent_time ON agent_invocations(agent_did, invoked_at DESC)
- idx_invocations_deployment ON agent_invocations(deployment_id)
- idx_metrics_time ON agent_metrics(timestamp DESC)

View:
- agent_stats as an aggregate joining deployments and invocations for quick per-agent counts and last invoked (keep simple).

### 2.7 services/runtime/src/agents/executor.py
Create `AgentExecutor` with:
- `async execute(agent_id:str, code:str, input_data:dict, timeout:int=30) -> dict` returning a dict for `InvocationResponse` fields.
- Use `asyncio.wait_for` for timeouts.
- Execute user code safely via `exec` in a restricted environment:
  - Provide ONLY safe builtins: `print, len, str, int, float, bool, dict, list, tuple, set, range, enumerate, zip, map, filter, sorted, sum, min, max, abs, round, isinstance, type`
  - Disable file/network/imports by omitting `__import__` and not providing os/sys.
- Run sync exec in thread pool: `loop.run_in_executor(None, self._sync_execute, code, safe_globals)`.
- The executed code must set `result` in its local scope; capture it.
- Cost estimate = `ceil(execution_time_ms / 1000.0) * 1` cent (i.e., $0.01/sec).
- Generate `invocation_id` deterministically from `agent_id + current time` (hashlib sha256 hex, truncated).

### 2.8 services/runtime/tests/test_executor.py
PyTest async tests:
- `test_simple_execution` (x + y)
- `test_string_operations`
- `test_timeout` (sleep beyond timeout) → ensure TIMEOUT
- `test_error_handling` (ZeroDivisionError) → ERROR
- `test_safe_environment` (attempt `import os`) → must fail/raise
- `test_cost_estimation` (mock quick vs slower runs) → cents as expected
Import `AgentExecutor` from `services.runtime.src.agents.executor`.

### 2.9 services/runtime/src/api/agents.py
FastAPI router: `router = APIRouter(prefix="/api/v1/agents", tags=["agents"])`
Endpoints:
1) POST `/deploy`
   - Accept `DeploymentRequest`
   - Insert into `agent_deployments` (store code in `code`, basic resource_limits JSON)
   - Return `DeploymentResponse` with status RUNNING (containerization later)
2) POST `/invoke`
   - Accept `InvocationRequest`
   - Fetch latest deployment for `agent_id` (map to agent_did same as agent_id for MVP)
   - Run executor.execute(...)
   - Insert into `agent_invocations`
   - Return `InvocationResponse`
3) GET `/{agent_id}/status`
   - Query deployments + invocations summary
   - Return `AgentStatusResponse` (use NULLs when unknown)
4) DELETE `/{agent_id}`
   - Mark latest deployment TERMINATED, set `stopped_at`
   - Return `{ "deleted": true }`
Use `HTTPException` for 404; handle DB errors cleanly.

### 2.10 services/runtime/src/api/health.py
Router `tags=["health"]`:
- GET `/health`:
  - Try `SELECT 1` via db
  - Return `HealthResponse(status="healthy"/"unhealthy", service="runtime-service", timestamp=now, checks={"database":bool, "executor": True})`
  - HTTP 200 if healthy, 503 otherwise.

### 2.11 services/runtime/src/main.py
- Build FastAPI app with lifespan:
  - on startup: `await db.connect()`
  - on shutdown: `await db.disconnect()`
- Title/description/version:
  - title="Agent Runtime Service"
  - description="Deploy and execute AI agents"
  - version="1.0.0"
- CORS allow all (for now).
- Include routers (agents, health).
- GET `/` returns basic service info (name, version, time).
- `if __name__ == "__main__":` run uvicorn with host/port from settings.

### 2.12 services/runtime/Dockerfile
- Base: `python:3.11-slim`
- `WORKDIR /app`
- Install system deps: `apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*`
- Copy `requirements.txt` then `pip install --no-cache-dir -r requirements.txt`
- Copy `src/` to `/app/src/`
- Create non-root user `runtime` (uid 1000), chown.
- `USER runtime`
- `EXPOSE 8000`
- `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`

### 2.13 k8s/08-runtime.yaml
Create:
- Namespace assumed: `agentos`
- Service (ClusterIP) `runtime` port 8000 selector `app: runtime`
- Deployment `runtime`:
  - replicas: 1
  - image: agentos/runtime:latest
  - container port: 8000
  - env (some from configmap/secret):
    * POSTGRES_HOST=postgres
    * POSTGRES_PORT=5432
    * POSTGRES_DB=agentos
    * POSTGRES_USER from secret `agentos-secrets` key `POSTGRES_USER`
    * POSTGRES_PASSWORD from secret `agentos-secrets` key `POSTGRES_PASSWORD`
    * REDIS_HOST=redis
    * DEBUG=false
  - resources:
    * requests: 200m CPU, 512Mi
    * limits: 500m CPU, 1Gi
  - livenessProbe/readinessProbe: HTTP GET `/health` port 8000 (initialDelaySeconds 30 for liveness, 5 for readiness)
  - labels: `app: runtime`

### 2.14 services/runtime/README.md
Include overview, features, setup, run locally, run tests, endpoints list, docker build/run, and k8s deploy commands exactly as in the spec.

### 2.15 Stubs
- `deployer.py` and `monitor.py` can be minimal placeholders with TODOs and type-hinted class skeletons.
- `test_deployer.py` and `test_api.py` can include simple smoke tests that import modules to ensure importability.

## 3) Test Scripts (under services/runtime/)
Create:
- `test_deploy.py`: uses httpx to POST to `http://localhost:8000/api/v1/agents/deploy` with payload from spec; prints response.
- `test_invoke.py`: POST to `/api/v1/agents/invoke` with input `{x:10,y:20}`, timeout 10; expect 30; print result.
- `test_status.py`: GET `/api/v1/agents/test-math-agent/status`; print summary.
- `test_e2e.py`: Deploy customer-support agent with the exact code snippet below, invoke 5 messages, check status increments, print formatted summary.
Agent code for e2e:
sentiment = "neutral"
if "bad" in input_data['message'].lower():
    sentiment = "negative"
elif "great" in input_data['message'].lower():
    sentiment = "positive"
result = {
    "message": input_data['message'],
    "sentiment": sentiment,
    "response": f"I understand your {sentiment} feedback"
}

## 4) Gateway Integration (Go) — minimal forwarding
- In `services/gateway/internal/router/routes.go` (or closest match), add reverse-proxy or forwarders:
  - POST `/api/v1/agents/deploy` → `http://runtime:8000/api/v1/agents/deploy`
  - POST `/api/v1/agents/invoke` → `http://runtime:8000/api/v1/agents/invoke`
  - GET  `/api/v1/agents/{id}/status` → `http://runtime:8000/api/v1/agents/{id}/status`
  - DELETE `/api/v1/agents/{id}` → `http://runtime:8000/api/v1/agents/{id}`
- Reuse existing middleware (auth, logging). Preserve headers/body.

## 5) Web UI Integration (React/TS, Tailwind)
- Create `services/web-ui/src/pages/DeployAgent.tsx`:
  - Form fields: Agent ID, Agent Code (monospace textarea), Max Memory (256m/512m/1g/2g), Max CPU (0.25/0.5/1/2).
  - Button “Deploy” → POST `/api/v1/agents/deploy` via axios (assume axios wrapper at `src/lib/api`).
  - Loading + success (deployment_id) + error states. Clean styling with Tailwind.
- Update `services/web-ui/src/App.tsx`:
  - Add route `/deploy` to DeployAgent.
  - Add nav link “Deploy Agent”.

## 6) Verification Checklist (create as comments at bottom of README)
- Day 1–2: structure, requirements, config, models, db, migration.
- Day 3–4: executor + tests, API, health, main.
- Day 5: Docker + K8s + README.
- Day 6–7: local run, tests, migration, docker build, k8s deploy, end-to-end.

## 7) Helpful Commands (append to README)
Local:
- `cd services/runtime && python -m uvicorn src.main:app --reload`
- Visit `http://localhost:8000/health` and `/docs`
Tests:
- `cd services/runtime && pytest -v`
Migrations (example):
- `kubectl port-forward -n agentos svc/postgres 5432:5432`
- `psql -h localhost -U agentos -d agentos -f infra/migrations/004_runtime_schema.sql`
Docker:
- `cd services/runtime && docker build -t agentos/runtime:latest .`
K8s:
- `kubectl apply -f k8s/08-runtime.yaml`
- `kubectl get pods -n agentos | grep runtime`
- `kubectl logs -n agentos -l app=runtime --tail=100 -f`

## 8) Final polish
- Ensure all Python files type-check and import cleanly.
- Ensure `/health` returns 200 when DB reachable; else 503 with checks.
- Print “Runtime service ready” at startup INFO logs.

# End of plan — execute all steps and write all files now.
