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