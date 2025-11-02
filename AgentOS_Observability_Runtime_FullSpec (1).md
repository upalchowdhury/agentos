# AgentOS — Unified Observability & Runtime PRD + Developer Workbook
_Last updated: 2025-11-02 23:58 UTC_

> **Purpose**  
> Single, implementation-ready source of truth for AgentOS MVP: PRD, user stories, acceptance criteria, test plans, execution checklists, and Windsurf/Claude Code build prompts.  
> Save as: `docs/product/AgentOS_Observability_Runtime_FullSpec.md`

---

## 1. Executive Summary
**Problem.** Teams run many agents across stacks (LangGraph, CrewAI, AutoGen, MCP, A2A, AgentForce, custom). They lack **production-grade visibility and control**: where time/tokens/cost go, why an agent made a decision, which sub-agent/tool call failed, and how to stop runaway behavior—*without ripping out existing gateways (e.g., MuleSoft Flex Gateway).*

**Solution.** AgentOS is a **vendor-agnostic runtime + registry + observability + governance plane** that can **coexist** with MuleSoft Agent Fabric / Flex Gateway or operate standalone.
- **Model A (Deploy-Here):** upload code; we host/execute. Full telemetry by default.
- **Model B (Register External):** keep your infra; install SDK **or** run an **Envoy/Flex-compatible sidecar** to emit deep telemetry.
- **Unified Observability:** reasoning-aware traces (invocation → step → tool), logs correlation, cost-attribution, and replay.
- **Governance:** OPA policies, obligations (redaction/allowlists/budget caps), protocol packs for **A2A/MCP**, and signed-call verification.
- **Enterprise Interop:** **ATP→OTel bridge** (Grafana/Datadog), **Flex sidecar** for “design for coexistence, not rip-and-replace,” and an **Exchange-style catalog** with quality badges.

**Strategic posture.** *Meet MuleSoft where they’re strong* (protocol governance at edge, catalog UX, OTel) and *beat them where they’re weak* (reasoning-aware traces, cost governance, deterministic replay, obligation trails, federated memory).

---

## 2. Goals & Non-Goals
### 2.1 Goals (MVP → v1)
1) Create/register an agent in < 5 minutes.  
2) Invoke & observe any agent with **step-level reasoning graph**.  
3) Drilldown UI: **Org → Project → Agent → Version → Invocation → Step**.  
4) Governance: **OPA** RBAC/ABAC + audit.  
5) **CostOps:** line item per invocation + MTD aggregates + budget caps.  
6) **Protocol Governance Parity:** **A2A/MCP** policy packs (signature verify, schema validation, allowlists, size caps).  
7) **Flex/Envoy Interop:** sidecar mode + **ATP→OTel** export for existing pipelines.  
8) **Exchange-style Catalog:** browse/search agents/tools/prompts with **Badges** (Verified Telemetry, Policy‑Clean, Cost‑Tagged).

### 2.2 Non-Goals (now)
- Public agent marketplace/discovery.  
- Advanced prompt experimentation beyond basic versioning/diff/approval.  
- Exact vendor token billing; use pluggable cost adapters + reconciliation.

---

## 3. Personas
- **Platform/SRE:** uptime, latency/error budgets, alerts, OTel/Grafana/Datadog compatibility.
- **Agent Developer:** debug, replay, step visibility, quick deploys.
- **Security/Compliance:** auditability, obligations, policy posture.
- **FinOps:** cost attribution (team/agent/version), budget caps & alerts.
- **Enterprise Architect:** keep Flex/Anypoint; add reasoning telemetry & OPA.

---

## 4. Deployment Models
### 4.1 Model A — Runtime (Deploy-Here)
- Upload code (10–50k chars) or ZIP + `requirements.txt`/`pyproject.toml`.
- Configure CPU/memory; deploy in ≤60s for small agents.
- Invoke via `/invoke` returning envelope and emitting **ATP** events.

### 4.2 Model B — Registry / Sidecar (Register External)
- Register external endpoint + auth + rate limits + health checks.
- **Telemetry paths (in descending richness):**  
  1) **SDK** (best) → Verified Telemetry badge; step-level traces.  
  2) **Envoy/Flex-compatible sidecar** (good) → deep telemetry with minimal app changes.  
  3) **Gateway/proxy fallback** (partial) → latency/status only; Partial Telemetry badge.

---

## 5. End-to-End Journeys
1) **Create (A):** Upload → deploy → `/invoke` → trace, logs, cost.  
2) **Register (B):** Register endpoint → install SDK or sidecar → first run shows **Verified Telemetry**.  
3) **Investigate:** SRE sees p95 spike → drilldown → slow tool identified → budget alert fired.  
4) **Govern:** OPA denies unauthorized invoke → 403 with `trace_id`; audit logged.  
5) **Replay:** Deterministic replay reproduces bug; prompt diff shows change; approval workflow.  
6) **Interop:** Flex mesh remains; AgentOS sidecar emits ATP; OTel collector ingests for shared dashboards.

---

## 6. Drilldown Model & Data
**Hierarchy:** Org → Project → Agent → Version → Invocation → Step → Tool Call  
**Trace Entities:** `trace_id`, `invocation_id`, `agent_id`, `version_id`, timings, status, cost, policy/obligation flags, redaction markers, protocol and signature posture.

---

## 7. Functional Requirements
### 7.1 Runtime (Model A)
- Upload/deploy/rollback/version immutability; code hash saved.
- Timeouts & concurrency caps; capped cost on overage.
- Envelope return with `trace_id`, latency, status, excerpts (redacted).

### 7.2 Registry & Sidecar (Model B)
- Register endpoint + auth, health probe, rate limits (429 on exceed).  
- SDK installer & sidecar manifests; telemetry quality badge (Verified/Partial).

### 7.3 Observability (ATP v0)
- Step-level traces (prompt|tool|subagent|system), timings, status, tokens, per-step cost.  
- Logs correlated by `trace_id`.  
- Per-invocation cost + MTD aggregates within SLO.

### 7.4 Governance
- **OPA RBAC/ABAC** on `/invoke`, `/deploy`, `/logs`.  
- **Obligations:** redaction, external-domain allowlists, budget caps.  
- **Audit log** for allow/deny and all invocations (exportable CSV/JSON).

### 7.5 Protocol Policy Packs (A2A/MCP)
- Prebuilt bundles: **signature verification**, **schema conformance**, **prompt size caps**, **PII scan**, **tool/domain allowlists**.  
- Hot-reload; org/project overrides; policy latency p95 < 5ms at gateway.

### 7.6 Flex / Envoy Interop
- **Sidecar mode** compatible with Flex Gateway/Envoy filter chain.  
- **ATP→OTel** mappings (traces/logs/metrics) with resource attrs (`agent_id`, `version_id`, `step_id`).  
- Managed or local/air‑gapped modes supported.

### 7.7 Exchange-Style Catalog UX
- Browse/search agents/tools/prompts with badges: **Verified Telemetry**, **Policy‑Clean**, **Cost‑Tagged**.  
- Filters: runtime, provider, protocol (A2A/MCP), compliance class, health.  
- Deep links to Agent Detail and Policies.

---

## 8. Non‑Functional Requirements
- **Ingest** p95 < 200ms; withstand **500 RPS** telemetry bursts (2 min) with no loss; 95% traces visible < 30s.
- **Availability** ≥ 99.5% MVP.
- **Security/Privacy:** multi‑tenant isolation, no secrets in logs, encryption at rest & in transit, principle of least privilege.
- **Air‑gapped**: batch SDK mode; local OTel collector.
- **Gateway throughput**: 10k RPS/node with <1ms steady policy overhead.
- **OTel**: collector v0.9+; Grafana/Datadog dashboards pre-wired.

---

## 9. Telemetry Schema — **ATP v0 (Extended)**
```yaml
trace:
  trace_id: string
  invocation_id: string
  org_id: string
  project_id: string
  agent_id: string
  version_id: string
  protocol: a2a|mcp|http|grpc
  policy_enforced: [string]       # policy IDs applied
  signature_verified: bool
  provider_adapter: string        # openai|anthropic|vertex|bedrock|custom
  start_ts: RFC3339
  end_ts: RFC3339
  status: success|error|timeout
  execution_time_ms: int
  cost_cents: int
  error_message: string?
steps:
  - step_id: string
    parent_step_id: string|null
    name: string
    kind: prompt|tool|subagent|system
    start_ts: RFC3339
    end_ts: RFC3339
    latency_ms: int
    gateway_latency_ms: int?
    model_provider: string?
    tokens_in: int?
    tokens_out: int?
    cost_cents: int?
    redaction_applied: bool?
    budget_enforced_cents: int?
    status: success|error|timeout
    error_type: string?
    error_message: string?
    input_excerpt: string?   # redacted
    output_excerpt: string?  # redacted
```

---

## 10. User Stories (Backlog with Acceptance Criteria)
> **Legend** Priority = **M** (Must) / **S** (Should) / **C** (Could).

### A. Runtime (Model A)
- **US-A1 (M)** Create & deploy agent  
  **As a** developer **I want** to upload code & requirements and deploy **so that** I can invoke it.  
  **Acceptance:** Deploy returns `deployment_id` & `version_id` ≤ 60s; version immutable; code hash saved.

- **US-A2 (M)** Invoke & view trace  
  **As a** developer **I want** an invocation to generate a step-level trace **so that** I can debug performance.  
  **Acceptance:** Waterfall/DAG shows ≥1 step; total latency equals `execution_time_ms` ±5%; error nodes visible.

- **US-A3 (M)** Cost attribution per invocation  
  **As** FinOps **I want** per-invocation cost **so that** I can allocate spend.  
  **Acceptance:** Cost in cents available within 10s; monthly aggregate = sum ±1%.

- **US-A4 (S)** Timeouts & concurrency caps  
  **As** platform **I want** per-agent timeout and concurrency **so that** I prevent runaway compute.  
  **Acceptance:** Overages return timeout/quota status; cost capped; metric increments.

### B. Registry / Sidecar (Model B)
- **US-B1 (M)** Register external agent  
  **As a** developer **I want** to register endpoint + auth + rate limit **so that** I can route calls via the gateway.  
  **Acceptance:** Health probe runs; status shown; 429s when exceeding configured rate.

- **US-B2 (M)** Install SDK for deep telemetry  
  **As a** developer **I want** to see step-level traces for external agents **so that** I can debug like Model A.  
  **Acceptance:** After SDK, **Verified Telemetry** badge; step traces visible.

- **US-B3 (S)** Proxy/sidecar fallback for partial telemetry  
  **As an** SRE **I want** partial telemetry via proxy/sidecar **so that** I get visibility without code changes.  
  **Acceptance:** Status & latency captured; UI shows **Partial Telemetry** badge.

### O. Observability
- **US-O1 (M)** Org/Project dashboards  
  **As an** SRE **I want** invocations, p95 latency, error rate, and cost charts **so that** I can spot issues fast.  
  **Acceptance:** Charts load <1.5s with last 24h data; deep link filters preserved.

- **US-O2 (M)** Trace explorer & logs correlation  
  **As a** developer **I want** logs correlated by `trace_id` **so that** I can move from steps to logs in one click.  
  **Acceptance:** Logs view defaults to current `trace_id`; pagination & levels work.

- **US-O3 (S)** Alerts (error% / latency)  
  **As an** SRE **I want** threshold alerts to Slack/email with deep links **so that** I respond quickly.  
  **Acceptance:** Trigger > threshold sends alert ≤ 60s; link opens with filter applied.

- **US-O4 (M)** ATP→OTel bridge  
  **As an** SRE **I want** ATP events mapped to OTel **so that** existing Grafana/Datadog dashboards work.  
  **Acceptance:** Spans map 1:1 with resource attrs; trace joins on `trace_id`.

- **US-D1 (M)** Deterministic replay  
  **As a** developer **I want** to replay an invocation with identical inputs/tools/models **so that** I can reproduce bugs.  
  **Acceptance:** Replay reproduces step graph unless external nondeterminism flagged.

### G. Governance
- **US-G1 (M)** OPA RBAC decisions on `/invoke`  
  **Acceptance:** Unauthorized invokes return 403 with `trace_id`; audit stores decision JSON.

- **US-G2 (S)** Obligations: redaction & allowlists  
  **Acceptance:** Redacted fields show `REDACTED`; blocked tool calls denied and logged.

- **US-G3 (S)** Audit export  
  **Acceptance:** Export ≤ 60s for 100k rows; CSV/JSON checksum provided.

- **US-G4 (M)** Protocol packs for A2A/MCP  
  **Acceptance:** Signed call verification blocks invalid signatures; deny logs carry `policy_id`, `trace_id`.

- **US-G5 (S)** Flex/Envoy interop  
  **Acceptance:** Dual-deploy validated on K8s; OTel exporter feeds existing pipeline.

### R. Registry Catalog
- **US-R1 (S)** Exchange-style catalog  
  **Acceptance:** Filtering by protocol/runtime; badges reflect telemetry & policy posture; deep links work.

---

## 11. Acceptance Tests (Scenarios)
### 11.1 E2E (MVP)
1) **A-Create-Invoke-Observe** — Create Model A agent; invoke success/error/timeout.  
   **Pass:** Traces reflect statuses; costs sum; logs correlate by `trace_id`.

2) **B-Register-SDK-Verify** — Register external echo; install SDK; invoke.  
   **Pass:** **Verified Telemetry** badge; step-level trace visible.

3) **B-Proxy/Sidecar-Partial** — Remove SDK; invoke via sidecar.  
   **Pass:** **Partial Telemetry** badge; duration & status only.

4) **OPA-RBAC** — Unauthorized user invokes restricted agent.  
   **Pass:** 403 with `trace_id`; audit shows `allow=false` and rule.

5) **Obligations-Redaction** — Payload includes PII.  
   **Pass:** Trace/logs show `REDACTED`; raw PII not stored.

6) **Alerts** — Induce error rate > threshold.  
   **Pass:** Slack alert with deep link to filtered view.

7) **Gateway-Interop** — Run A2A & MCP flows through (a) AgentOS gateway, (b) Flex+AgentOS sidecar.  
   **Pass:** Policy parity; identical allow/deny outcomes; perf within NFRs.

8) **OTel-Bridge** — Verify ATP→OTel mapping renders in collector/dashboards.  
   **Pass:** Spans/logs/metrics appear; attributes populated; joins OK.

9) **Replay** — Deterministic replay reproduces bug.  
   **Pass:** Same step graph & outputs; nondeterminism flagged when present.

### 11.2 Performance
- **Ingest spike** 500 RPS for 2 min → no loss; 95% traces visible < 30s.  
- **UI load** 10k invocations/day → lists & traces < 2s (pagination/sampling).

### 11.3 Security/Privacy
- No secrets in logs/traces; multi-tenant isolation enforced (403 + audit).

---

## 12. KPIs
- **TTF-Observe:** first trace visible < 10 min from setup.  
- **Debug time:** p95 time to identify failing step < 5 min.  
- **Verified coverage:** ≥ 70% agents with **Verified Telemetry** by week 4.  
- **Cost accuracy:** monthly aggregate within 2% of provider bills.  
- **Policy efficacy:** 100% restricted invocations denied.  
- **Protocol compliance rate:** ≥ 99.9% valid signatures on compliant traffic.  
- **Interop coverage:** ≥ 90% deployments can **coexist** with Flex/Envoy.

---

## 13. Execution Plan (Phases)
| Phase | Duration | Deliverables |
|------|----------|--------------|
| **1 (MVP)** | 2–3 wks | Model A runtime, ATP ingest, Trace/Logs, per-invocation cost, OPA allow/deny, basic alerts |
| **1.5 (Interop)** | 2 wks | A2A/MCP policy packs, ATP→OTel exporter |
| **2 (Registry & Sidecar)** | 3–4 wks | Model B registry + SDK + sidecar, health checks, rate limits, dashboards |
| **2.5 (Catalog)** | 2 wks | Exchange-style catalog UI + badges |
| **3 (Replay & Memory)** | 4+ wks | Deterministic replay, prompt diff/approval, federated memory beta |
| **4 (Optimization)** | ongoing | Risk scoring, ROI analytics |

---

## 14. Issue/Ticket Matrix (Importable)
| ID | Title | Area | Priority | AC Summary | Owner | Links |
|----|-------|------|----------|------------|-------|-------|
| US-A1 | Deploy Model A agent | Runtime | M | Deploy ≤60s; version immutable |  |  |
| US-A2 | Invocation trace explorer | Observability | M | Waterfall/DAG; latency matches ±5% |  |  |
| US-A3 | Cost per invocation | Observability | M | Cost within 10s; MTD = sum ±1% |  |  |
| US-A4 | Timeout & concurrency caps | Runtime | S | Overages handled, capped cost |  |  |
| US-B1 | Register external agent | Registry | M | Health, rate limit, status |  |  |
| US-B2 | SDK deep telemetry | Registry | M | Verified badge; step traces |  |  |
| US-B3 | Proxy/Sidecar partial telemetry | Registry | S | Partial badge; duration/status |  |  |
| US-O1 | Org/Project dashboards | Observability | M | Charts <1.5s; deep links |  |  |
| US-O2 | Logs correlation | Observability | M | Filter by trace_id |  |  |
| US-O3 | Alerts (error/latency) | Observability | S | Slack/email with deep link |  |  |
| **US-O4** | **ATP→OTel bridge** | **Observability** | **M** | Spans/logs/metrics parity |  |  |
| US-G1 | OPA RBAC on invoke | Governance | M | 403 + audit on deny |  |  |
| US-G2 | Obligations redaction/allowlist | Governance | S | REDACTED + deny blocked tools |  |  |
| US-G3 | Audit export | Governance | S | 100k rows ≤60s |  |  |
| **US-G4** | **A2A/MCP policy packs** | **Governance** | **M** | Sig verify + schema checks |  |  |
| **US-G5** | **Flex/Envoy interop** | **Gateway** | **S** | Sidecar mode; OTel export |  |  |
| **US-R1** | **Exchange-style catalog** | **Registry** | **S** | Browse/search + badges |  |  |
| **US-D1** | **Deterministic replay** | **Observability** | **M** | Reproduce identical step graph |  |  |

---

## 15. Checklists
### 15.1 MVP Readiness
- [ ] Model A deploy/invoke operational  
- [ ] ATP v0 events ingested  
- [ ] Trace explorer & logs correlation  
- [ ] Cost per invocation & MTD aggregate  
- [ ] OPA allow/deny wired in gateway  
- [ ] Alerts to Slack (error/latency)  
- [ ] Privacy: redaction verified  
- [ ] Multi-tenant isolation verified

### 15.2 Interop Readiness
- [ ] A2A/MCP policy packs validated  
- [ ] ATP→OTel bridge emits spans/logs/metrics  
- [ ] Flex/Envoy sidecar deploy tested on K8s  
- [ ] Envoy filters benchmarked to NFRs

### 15.3 Launch Ops
- [ ] Runbooks: **RUNBOOK_local.md**  
- [ ] OpenAPI synced (**openapi/api.yaml**)  
- [ ] Sample agents (A/B) demo-ready  
- [ ] Dashboards pre-configured  
- [ ] Seed data for sandbox org  
- [ ] Catalog demo items with badges

---

## 16. Appendices
### 16.A UI Information Architecture
- **Agents List** → **Agent Detail** (Overview · Invocations · Trace · Logs · Metrics · Policies · Audit)  
- **Create Agent**: Toggle **Model A vs Model B**; show SDK command or Flex sidecar snippet.  
- **Badges**: **Verified Telemetry** (SDK/Sidecar) / **Partial Telemetry** (Proxy) / **Policy‑Clean** / **Cost‑Tagged**.  
- **Catalog**: Grid/list; filters: runtime, provider, protocol, compliance; health & posture indicators.

### 16.B Directory Layout (Windsurf)
```
agentos/
├── services/
│   ├── runtime/
│   ├── registry/
│   ├── gateway/            # Envoy/Flex-compatible filters + OPA ext-authz
│   ├── observability/
│   │   ├── ingest/         # ATP ingest → Kafka/ClickHouse/OLAP
│   │   ├── o11y-bridge/    # ATP → OTel exporter
│   │   └── api/            # FastAPI for traces/logs/metrics
│   ├── policy/             # OPA bundles + obligations
│   ├── web-ui/             # Svelte/React app
│   └── identity/
├── infra/
│   ├── k8s/
│   ├── migrations/
│   └── terraform/
└── docs/
    └── product/
        └── AgentOS_Observability_Runtime_FullSpec.md
```

### 16.C Key API Endpoints (initial)
- `POST /api/agents/register` — register external agent (Model B)  
- `POST /api/runtime/deploy` — upload & deploy (Model A)  
- `POST /api/invoke/:agent_id` — invoke entrypoint  
- `POST /api/telemetry/events` — ingest ATP events  
- `GET /api/traces/:trace_id` — trace with steps  
- `GET /api/logs?trace_id=` — logs correlation  
- `POST /api/policy/evaluate` — OPA decision endpoint  
- `GET /api/cost/summary` — FinOps summary  
- `GET /api/catalog/search` — assets + badges

### 16.D Data Models (storage sketch)
- `agent_registry(agent_id, owner, runtime, protocol, policy_class, health)`  
- `telemetry_events(trace_id, step_id, kind, timings, status, tokens, cost, policy_flags)`  
- `policy_audit(id, trace_id, policy_id, allow, obligations, ts)`  
- `alerts(id, type, severity, agent_id, version_id, ts, context)`  
- `stored_prompts(id, version, diff, approver, ts)`

### 16.E Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Partial telemetry without SDK | Sidecar option + **Verified** badge gating features |
| PII leakage | Obligations at ingest + UI masking + policy tests |
| Cost drift vs vendor bills | Versioned adapters + monthly reconciliation job |
| Trace volume explosion | Success sampling; full failure traces |
| Flex policy conflict | Shared OPA bundle interop tests; scoped filter chains |

### 16.F Claude Code / Windsurf Build Prompt (Copy-Paste)
```
You are an expert repo refactorer and code generator. Implement the AgentOS MVP per
docs/product/AgentOS_Observability_Runtime_FullSpec.md.

SCOPE (Phase 1 + 1.5):
- Model A runtime: deploy small Python agents (FastAPI worker), version immutability, timeout & concurrency caps.
- ATP ingest service (FastAPI) with ClickHouse (or Postgres + Timescale) for telemetry_events.
- Trace explorer API: GET /api/traces/:trace_id, logs correlation via trace_id.
- CostOps: per-invocation cost calc (adapters: openai, anthropic, vertex, bedrock), MTD aggregates.
- OPA gateway: ext-authz for /invoke; obligations (redaction, allowlists, budget caps).
- Alerts: error% and latency thresholds → Slack webhook (config yaml).
- Protocol policy packs: A2A/MCP signature verify + schema checks.
- ATP→OTel exporter service: map ATP spans/logs/metrics to OTel collector.

DELIVERABLES:
- services/runtime, services/observability/{ingest,o11y-bridge,api}, services/policy, services/gateway, services/web-ui.
- OpenAPI spec under openapi/api.yaml.
- Seed data + demo agents (Model A + Model B echo).
- Unit tests: pytest for cost adapters, OPA decisions, ATP mapping; Playwright for trace UI smoke.
- K8s manifests under infra/k8s (local kind cluster works).

CONSTRAINTS:
- No secrets in logs; redact PII.
- Target p95 ingest <200ms; basic load: 500 RPS burst for 2 min.
- Ensure Envoy/Flex sidecar manifest available; provide OPA bundle + filter chain examples.
```

---

## 17. Completion Definition (Exit Criteria)
- APIs documented (OpenAPI).  
- Telemetry & audit visible in Grafana/Datadog via OTel.  
- CI runs unit + integration tests; baseline load test passes.  
- UI integrated with live APIs; sample agents demo-ready.  
- Flex/Envoy interop validated on a sample mesh (sidecar).  

---

**End of document.**
