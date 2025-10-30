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






Context (very important):
The repo agentos already exists and partly works. Do not refactor or rename existing working services unless explicitly instructed. Add the features below with minimal invasive changes, clean boundaries, and strong tests.

Absolute rules:

If a change violates the rules or leaves tests flakey → stop and propose a fix.

Keep PRs atomic by domain (runtime, gateway, web-ui, governance, observability).

Every new endpoint must be in the OpenAPI spec + e2e test + RBAC policy + audit log.

Prefer OPA for authZ; never hardcode policy logic in app code.

No secrets in code; use env + K8s secrets.

Ship with working make targets and local k8s (kind or k3d).

0) Repo Layout (assume exists)
agentos/
├── services/
│   ├── identity/          # OIDC, tokens (exists)
│   ├── gateway/           # API gateway (exists)
│   ├── runtime/           # NEW: build/run agents (Model A)
│   ├── registry/          # NEW: external agents (Model B)
│   ├── observability/     # NEW: cost, metrics, logs API shims
│   └── web-ui/            # UI (exists)
├── infra/
│   ├── migrations/        # DB migrations (exists)
│   └── opa/               # NEW: policy bundles (.rego)
├── k8s/                   # manifests/helm (exists)
├── openapi/               # NEW: unified api.yaml
├── ops/                   # NEW: make, scripts, kind cluster, seed data
└── docs/                  # NEW: runbooks & ADRs

1) Features to Implement (Incremental, in this order)
1.1 Model A — Code Upload & Deploy (Runtime Service)

Goal: Developer uploads Python code (LangChain or plain), declares deps/env, gets a HTTPS /invoke endpoint running on our K8s.

Add:

services/runtime/ (Python FastAPI or Go — pick what matches repo standards)

Buildpacks/Dockerfile template to containerize uploaded code

Job/Deployment controller for per-agent pods

Storage for code blobs (S3/minio); signed URLs for upload

Resource limits (CPU/mem) per deployment

Execution shim that guarantees contract:

Input: JSON input_data

Output: JSON { result: any, cost: number, execution_time_ms: number, metadata: object }

API (add to openapi/api.yaml):

POST /v1/agents/modelA
  - body: { name, runtime: "python3.11", requirements: string[], env: {k:v}, resources:{cpu,mem} }
  - returns: { agent_id, upload_url, deployment_id }

PUT /v1/agents/{agent_id}/artifact
  - body: multipart/form-data (zip or code text)
  - effect: build image, deploy, status: PENDING→READY

GET /v1/agents/{agent_id}
  - status, endpoints, version, owner, rbac, cost_to_date

POST /v1/agents/{agent_id}/invoke
  - body: { input_data: any }
  - returns execution envelope (above)


DB (new tables & migrations under infra/migrations/):

agents (id, name, owner_id, model_type enum[A|B], status, runtime, image_ref, created_at)

agent_versions (id, agent_id, artifact_uri, requirements_json, env_json, resources_json, image_ref, created_at)

invocations (id, agent_id, version_id, requester_id, input_hash, started_at, ended_at, cost_decimal, status, error_json)

cost_snapshots (id, agent_id, period_start, period_end, total_cost)

K8s (in k8s/runtime/):

Deployment for runtime service

Job/Deployment templates for agent workloads

ServiceAccount + RBAC for image pulls, Jobs, Pods

HPA on QPS / CPU

Make targets (in ops/Makefile):

make runtime/dev (run service locally)

make runtime/deploy (apply k8s)

make seed (create demo agent)

Acceptance:

Upload zip → build → ready in < 5 min

curl invoke returns envelope with execution_time_ms, cost

Logs & metrics visible (see §1.3)

1.2 Model B — External Agent Registry & Proxy

Goal: Register external endpoints (OpenAI Assistants, Agentforce, MCP, custom HTTP) and route via our gateway with RBAC, rate limits, audit.

Add:

services/registry/ (FastAPI/Go)

Registration flow (name, endpoint_url, auth_scheme, headers/token)

Health checks & SLO status

Proxy client in services/gateway/ that enforces OPA decisions

API additions (openapi/api.yaml):

POST /v1/agents/modelB
  - body: { name, endpoint_url, auth: { type: bearer|header, value|header_name }, rate_limit:{rps, burst} }
  - returns: { agent_id }

POST /v1/agents/{agent_id}/invoke
  - body: { input_data: any }
  - effect: gateway → registry proxy → external endpoint


DB:

Extend agents with endpoint_url, auth_json, rate_limit_json, health_status

K8s:

registry deployment + secrets for outbound signing if needed

Acceptance:

Register dummy httpbin echo agent

Invoke through gateway with RBAC + audit log

Rate limits enforced (429)

1.3 Observability & Cost (Unified)

Goal: Unified logs/metrics/costs per agent & per invocation.

Add:

services/observability/ (API façade over Loki/ELK + Prometheus + cost calc)

Sidecar or SDK to emit:

invocation_started, invocation_finished

tokens_used, provider="openai|gemini|..." (if available)

Cost calculator plugin: provider-aware pricing adapters

Web-UI dashboards (charts: invocations, p50/p95 latency, error rate, cost)

API (openapi/api.yaml):

GET /v1/agents/{agent_id}/metrics?range=1d
GET /v1/agents/{agent_id}/logs?range=1h&level=error
GET /v1/agents/{agent_id}/costs?period=month


Acceptance:

Invoke test agent 10x → charts update

See error sample in logs view

Cost line-item per invocation & monthly aggregate

1.4 RBAC + OPA Policies (Zero-Trust)

Goal: Centralized policy: who/what can invoke which agent; agent→agent (A2A) permissions; obligations (masking, PII checks).

Add:

infra/opa/ with policy bundles:

invoke_allow.rego (subject, resource, action)

obligations.rego (redaction flags, content filter requirements)

Gateway must call OPA before any /invoke:

Input: { subject, agent_id, action:"invoke", caller_agent_id? }

Output: { allow:bool, obligations:{ ... } }

Content filter hook (stub) that executes obligations

Acceptance:

A regular user without role cannot invoke a restricted agent

An agent with A2A permission can call another agent; denial otherwise

All decisions logged for audit

1.5 A2A (Agent→Agent) Routed Invocations

Goal: Allow agent code to call invoke_agent("<id>", payload) via a signed internal call through the gateway with OPA checks.

Add:

Runtime SDK (tiny lib) that exposes invoke_agent hitting gateway with a short-lived agent token (issued by identity service)

Gateway validates agent token, applies OPA, forwards call to target agent (Model A or B)

Acceptance:

Demo agent A calls B and B calls C (external): full audit trail captured

1.6 Web-UI (New Pages/Flows)

In services/web-ui/ add:

Dashboard

Cards: total agents, invocations 24h, error rate, monthly cost

Charts: invocations over time, p95 latency, cost over time

Agents List

Columns: name, model (A/B), status, owner, last deploy, cost MTD

Actions: View, Invoke, Disable

Agent Detail

Tabs:

Overview (endpoint, model, status)

Code (Model A): editor, requirements, env vars, resources, deploy button

Registry (Model B): endpoint, auth, health, rate-limit

Metrics (charts)

Logs (search, levels)

Policies (attach RBAC roles; view OPA rules)

Create Agent

Toggle: Model A vs Model B

Model A: upload ZIP or paste code; requirements; env; resources

Model B: endpoint url; auth; health probe; rate-limit

Invocation Console

JSON editor for input

Run → streaming output & metadata panel

UX rules:

Don’t block UI on build; show “Build & Deploy” job with status stream

For env vars: masked, copy-disabled after save

For logs: infinite scroll + level filter

Acceptance:

Full happy-path flows work for A and B

Errors are user-friendly and actionable

2) OpenAPI — Minimal Spec Skeleton (extend as you implement)

Create openapi/api.yaml and keep it as the single source of truth. Example starters:

openapi: 3.0.3
info:
  title: Agent Economy OS API
  version: 0.1.0
servers:
  - url: https://api.local.agentos
paths:
  /v1/agents/modelA:
    post:
      summary: Create Model A agent
      requestBody: { required: true, content: { application/json: { schema: { $ref: '#/components/schemas/CreateModelA' } } } }
      responses: { '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/Agent' } } } } }
  /v1/agents/modelB:
    post:
      summary: Create Model B agent
      requestBody: { required: true, content: { application/json: { schema: { $ref: '#/components/schemas/CreateModelB' } } } }
      responses: { '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/Agent' } } } } }
  /v1/agents/{agent_id}/invoke:
    post:
      summary: Invoke agent (A or B)
      parameters: [{ in: path, name: agent_id, required: true, schema: { type: string } }]
      requestBody: { required: true, content: { application/json: { schema: { type: object, additionalProperties: true } } } }
      responses:
        '200': { description: OK, content: { application/json: { schema: { $ref: '#/components/schemas/InvocationResult' } } } }
components:
  schemas:
    CreateModelA:
      type: object
      required: [name, runtime]
      properties:
        name: { type: string }
        runtime: { type: string, enum: [python3.11] }
        requirements: { type: array, items: { type: string } }
        env: { type: object, additionalProperties: { type: string } }
        resources: { type: object, properties: { cpu: { type: string }, mem: { type: string } } }
    CreateModelB:
      type: object
      required: [name, endpoint_url]
      properties:
        name: { type: string }
        endpoint_url: { type: string }
        auth: { type: object, additionalProperties: true }
        rate_limit: { type: object, properties: { rps: { type: number }, burst: { type: number } } }
    Agent:
      type: object
      properties:
        agent_id: { type: string }
        model_type: { type: string, enum: [A,B] }
        status: { type: string }
    InvocationResult:
      type: object
      required: [result, execution_time_ms]
      properties:
        result: { type: object, additionalProperties: true }
        cost: { type: number }
        execution_time_ms: { type: integer }
        metadata: { type: object, additionalProperties: true }

3) Security, Identity, and RBAC

Reuse services/identity/ for JWTs. Add agent tokens (short-lived) for A2A.

Add OPA bundle server (sidecar or central) under infra/opa/.

Gateway must check:

Human token OR agent token

OPA decision (allow/deny + obligations)

Add content filter hook (placeholder) that enforces obligations (e.g., PII redaction flags).

4) Cost & Pricing Scaffolding

Pricing adapters: OpenAI, Anthropic, Gemini, local LLMs (stub).

Calculation: cost = tokens * price_per_token + infra_seconds * price_per_second.

Persist per-invocation; aggregate nightly into cost_snapshots.

Web-UI shows: Free tier counters, Pro thresholds (stub values).

5) Kubernetes: Local & Dev

Provide ops/kind/ with cluster creation script, ingress, local domain *.agentos.

k8s/:

Namespace agentos

Deployments for gateway, runtime, registry, observability, identity

Ingress routes:

api.local.agentos → gateway

logs.local.agentos → grafana/loki (dev only)

Secrets via kubectl create secret or SOPS (document in docs/secrets.md).

6) Developer Experience

ops/Makefile:

make dev (run all services locally with hot reload or tilt/skaffold)

make kind-up / make kind-down

make migrate (run all migrations)

make test (unit + e2e)

make seed (create demo agents: LangChain A, httpbin B)

docs/:

RUNBOOK_local.md (1-page: start cluster, deploy, create agent, invoke)

ADR-0001-runtime-choice.md

7) Tests (you must add)

Unit: runtime build planner, registry signer, OPA client, cost calc

Integration: upload → build → deploy → invoke (A); register → proxy (B)

E2E (pytest/playwright):

UI flow: create A agent, deploy, invoke; charts update

UI flow: create B agent, invoke; see audit trail

A2A scenario: A→B allowed; A→C denied by OPA

CI pipeline runs tests on PR

8) Example cURL (used in e2e fixtures)
# Create Model A
curl -s -X POST https://api.local.agentos/v1/agents/modelA \
  -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name":"sarah-support-bot",
    "runtime":"python3.11",
    "requirements":["langchain","openai"],
    "env":{"OPENAI_API_KEY":"${OPENAI_API_KEY}"},
    "resources":{"cpu":"500m","mem":"1Gi"}
  }'

# Upload artifact (zip) then invoke
curl -s -X POST https://api.local.agentos/v1/agents/AGENT_ID/invoke \
  -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
  -d '{ "input_data": { "message": "I cant login", "customer_id": "CUST-456" } }'

9) Guardrails / Non-Goals

Don’t add Node.js runtime yet (Phase 2).

Don’t ship marketplace or public sharing.

No vendor lock to a single LLM provider; keep adapters.

10) Definition of Done (hard)

Model A: Upload → build → deploy → invoke returns { result, cost, execution_time_ms }.

Model B: Register external endpoint → gateway → invoke with RBAC + audit.

OPA: Deny/allow decisions for user and A2A; obligations plumbed.

Observability: UI charts for invocations, latency, errors; logs view; cost per agent.

A2A: invoke_agent() works with agent tokens and OPA.

Docs: RUNBOOK_local, OpenAPI, Make targets, sample env/secret instructions.

Tests: Unit + integration + e2e are green in CI.

11) First PR Checklist (Runtime MVP)

 services/runtime/ with build+deploy pipeline and execution shim

 DB migrations for agents, agent_versions, invocations

 openapi/api.yaml endpoints for create/invoke (A)

 k8s/runtime/ manifests + HPA

 ops/Makefile targets (runtime/dev, runtime/deploy)

 E2E: upload→invoke happy path green

Deliver these in small, reviewable PRs in this exact order.
If anything is ambiguous, propose 1–2 concrete options with pros/cons and proceed with the minimally invasive choice that meets the DoD.

Begin now.