# AgentOS — Observability & Runtime PRD + User Stories Workbook
_Last updated: 2025-10-30 02:20 UTC_

This workbook is the implementation-ready source for planning and tracking the AgentOS MVP. It includes the PRD, user stories (with priorities and acceptance criteria), test plans, and execution checklists. Copy this into your repo as `docs/product/AgentOS_PRD_UserStories_Workbook.md` or import into your tracker.

---

## 1) Executive Summary
**Problem.** Teams run many agents across stacks (LangGraph, CrewAI, AutoGen, MCP, A2A, AgentForce, custom). They lack **production-grade visibility**: where time/tokens/cost go, why an agent made a decision, which sub-agent/tool call failed, and how to stop runaway behavior.

**Solution.** AgentOS is a **vendor-agnostic runtime + registry + observability plane**:
- **Model A (Deploy-Here)**: upload code, we host/execute. Full telemetry by default.
- **Model B (Register External)**: point us to any externally-hosted agent; enforce RBAC and capture telemetry via **lightweight SDK or proxy**.
- **Unified Observability**: tracing, drilldowns, logs, metrics, costs, audits—like AppDynamics/Datadog, but **reasoning-aware**.

**Why now.** Agent orchestration is exploding; there is no cross-platform reasoning telemetry standard. We define an **Agent Telemetry Protocol (ATP)** and become the default control plane.

---

## 2) Goals & Non-Goals
### Goals (MVP → v1)
1) Create agents (A) or register agents (B) in <5 minutes.
2) Invoke & observe any agent with **traceable reasoning graph** (invocation → steps → tool calls).
3) Drilldown UI like AppDynamics/Datadog: org → project → agent → version → invocation → step.
4) Governance: RBAC via OPA; audit log for all invocations.
5) CostOps: line-item per invocation + monthly aggregates.

### Non-Goals (now)
- Marketplace/discovery of public agents.
- Advanced prompt experimentation beyond basic versioning.
- Exact token-level pricing across vendors (pluggable adapters only).

---

## 3) Personas
- **Platform Lead / SRE:** uptime, latency, error budgets, cost controls.
- **Agent Developer:** debug, replay, step visibility, quick deploys.
- **Security/Compliance:** auditability, RBAC, PII/obligations.
- **Finance/FinOps:** cost attribution (team/agent/version).

---

## 4) Model B (Register External) — Feasibility & Value
- **Feasible if** we require one of: (1) **SDK** (best), (2) **Gateway proxy** (good), (3) **Webhook/batch** (fallback).
- **Value:** very high—customers keep their infra and still get a single pane of glass + OPA.
- **Limits:** without SDK, only shallow metrics. **Decision:** ship Model A + Model B (SDK + proxy) in MVP; badge telemetry quality (Verified vs Partial).

---

## 5) End-to-End Journeys
1) **Create (A):** Upload code + reqs → deploy → `/invoke` → test → see trace, logs, cost.
2) **Register (B):** Register external endpoint + token → install SDK → first invocation shows verified telemetry.
3) **Investigate:** SRE sees p95 spike → drilldown → slow tool identified → budget alert.
4) **Govern:** Security policy enforced by OPA; redaction obligations applied; audit trail intact.

---

## 6) Drilldown Model (Mapping to AppDynamics/Datadog)
**Hierarchy:** Org → Project → Agent → Version → Invocation → Step → Tool Call  
**Trace Data:** `trace_id`, `invocation_id`, `agent_id`, `version_id`, timings, status, cost, excerpts (redacted).

---

## 7) Functional Requirements
### 7.1 Model A (Runtime)
- Upload code (10–50k chars) or ZIP + requirements.
- Configure CPU/mem, deploy in < 60s for small agents.
- `/invoke` endpoint returns execution envelope and emits ATP events.

### 7.2 Model B (Registry)
- Register endpoint + auth + rate limits.
- SDK installer for deep telemetry; proxy fallback for partial visibility.
- Health checks & SLO status.

### 7.3 Observability (ATP v0)
- Step-level traces (prompt/tool/subagent/system), timings, status, optional tokens + per-step cost.
- Logs correlated by `trace_id`.
- Cost per invocation + MTD aggregate.

### 7.4 Governance
- RBAC via OPA (invoke/deploy/logs).
- Obligations: redaction, external domain allowlist, budget caps.
- Audit log for all allow/deny decisions and invocations.

---


## 8) Non-Functional Requirements
- p95 ingest < 200ms; handle 500 RPS telemetry bursts.
- Availability 99.5% MVP.
- Multi-tenant isolation; privacy by default (no secret logging).
- Works in VPC/air‑gapped (SDK batch mode later).

---

## 9) Telemetry Schema (ATP v0 — Minimal)
```yaml
trace:
  trace_id: string
  invocation_id: string
  org_id: string
  project_id: string
  agent_id: string
  version_id: string
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
    model_provider: string?
    tokens_in: int?
    tokens_out: int?
    cost_cents: int?
    status: success|error|timeout
    error_type: string?
    error_message: string?
    input_excerpt: string?    # redacted
    output_excerpt: string?   # redacted
```

---

## 10) User Stories (Backlog with Acceptance Criteria)

> **Legend** Priority = M (Must) / S (Should) / C (Could) — mapped to MVP scope.

### A. Runtime (Model A)
- **US-A1 (M)** Create & deploy agent  
  **As a** developer **I want** to upload code & requirements and deploy **so that** I can invoke it.  
  **Acceptance:** Deploy returns `deployment_id` & `version_id` ≤ 60s for small code; version immutable; code hash saved.

- **US-A2 (M)** Invoke & view trace  
  **As a** developer **I want** an invocation to generate a step-level trace **so that** I can debug performance.  
  **Acceptance:** Waterfall/DAG shows ≥1 step; total latency equals `execution_time_ms` ±5%; error nodes visible.

- **US-A3 (M)** Cost attribution per invocation  
  **As** FinOps **I want** per-invocation cost **so that** I can allocate spend.  
  **Acceptance:** Cost in cents available within 10s; monthly aggregate = sum ±1%.

- **US-A4 (S)** Timeouts & concurrency caps  
  **As** platform **I want** per-agent timeout and concurrency **so that** I prevent runaway compute.  
  **Acceptance:** Overage returns timeout/quota status; cost capped; metric increments.

### B. Registry (Model B)
- **US-B1 (M)** Register external agent  
  **As a** developer **I want** to register endpoint + auth + rate limit **so that** I can route calls via the gateway.  
  **Acceptance:** Health probe runs; status shown; 429s when exceeding configured rate.

- **US-B2 (M)** Install SDK for deep telemetry  
  **As a** developer **I want** to see step-level traces for external agents **so that** I can debug like Model A.  
  **Acceptance:** After SDK, **Verified Telemetry** badge; step traces visible.

- **US-B3 (S)** Proxy fallback for partial telemetry  
  **As an** SRE **I want** partial telemetry via proxy **so that** I get some visibility without SDK.  
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

### G. Governance
- **US-G1 (M)** OPA RBAC decisions on /invoke  
  **As** Security **I want** centralized allow/deny **so that** access is controlled.  
  **Acceptance:** Unauthorized invokes return 403 with `trace_id`; audit stores decision JSON.

- **US-G2 (S)** Obligations: redaction & allowlists  
  **As** Security **I want** PII redaction and external domain allowlists **so that** data hygiene is enforced.  
  **Acceptance:** Redacted fields show `REDACTED`; blocked tool calls denied and logged.

- **US-G3 (S)** Audit export  
  **As** Compliance **I want** export of audit events for period **so that** I can satisfy reviews.  
  **Acceptance:** Export ≤ 60s for 100k rows; CSV/JSON checksum provided.

---

## 11) Acceptance Tests (Scenarios)
### E2E (MVP)
1) **A-Create-Invoke-Observe**  
   Create Model A agent; invoke success/error/timeout.  
   **Pass:** Traces reflect statuses; costs sum; logs correlate by `trace_id`.

2) **B-Register-SDK-Verify**  
   Register external echo; install SDK; invoke.  
   **Pass:** **Verified Telemetry** badge; step-level trace visible.

3) **B-Proxy-Partial**  
   Remove SDK; invoke via gateway.  
   **Pass:** **Partial Telemetry** badge; duration & status only.

4) **OPA-RBAC**  
   Unauthorized user invokes restricted agent.  
   **Pass:** 403 with `trace_id`; audit shows `allow=false`.

5) **Obligations-Redaction**  
   Payload includes PII.  
   **Pass:** Trace/logs show `REDACTED`; raw PII not stored.

6) **Alerts**  
   Induce error rate > threshold.  
   **Pass:** Slack alert with deep link to filtered view.

### Performance
- **Ingest spike** 500 RPS for 2 min → no loss; 95% traces visible < 30s.
- **UI load** Agent with 10k invocations/day → lists & traces < 2s (pagination/sampling).

### Security/Privacy
- No secrets in logs/traces; multi-tenant isolation enforced (403 + audit).

---

## 12) KPIs
- **TTF-Observe**: first trace visible < 10 min from setup.  
- **Debug time**: p95 time to identify failing step < 5 min.  
- **Coverage**: ≥ 70% agents with **Verified Telemetry** by week 4.  
- **Cost accuracy**: monthly aggregate within 2% of provider bills.  
- **Policy efficacy**: 100% restricted invocations denied.

---

## 13) Execution Plan (Phases)
**Phase 1 (2–3 wks):** Model A, ATP v0 ingest, Trace/Logs, per-invocation cost, OPA allow/deny, basic alerts.  
**Phase 2 (3–4 wks):** Model B registry + SDK + proxy, health checks, rate limits, dashboards.  
**Phase 3 (4+ wks):** A2A signed calls, obligations catalog, replay, prompt diffing, richer cost adapters.

---

## 14) Issue/Ticket Matrix (Importable)
| ID | Title | Area | Priority | AC Summary | Owner | Links |
|----|-------|------|----------|------------|-------|-------|
| US-A1 | Deploy Model A agent | Runtime | M | Deploy ≤60s; version immutable |  |  |
| US-A2 | Invocation trace explorer | Observability | M | Waterfall/DAG; latency matches ±5% |  |  |
| US-A3 | Cost per invocation | Observability | M | Cost within 10s; MTD = sum ±1% |  |  |
| US-A4 | Timeout & concurrency caps | Runtime | S | Overages handled, capped cost |  |  |
| US-B1 | Register external agent | Registry | M | Health, rate limit, status |  |  |
| US-B2 | SDK deep telemetry | Registry | M | Verified badge; step traces |  |  |
| US-B3 | Proxy partial telemetry | Registry | S | Partial badge; duration/status |  |  |
| US-O1 | Org/Project dashboards | Observability | M | Charts <1.5s; deep links |  |  |
| US-O2 | Logs correlation | Observability | M | Filter by trace_id |  |  |
| US-O3 | Alerts (error/latency) | Observability | S | Slack/email with deep link |  |  |
| US-G1 | OPA RBAC on invoke | Governance | M | 403 + audit on deny |  |  |
| US-G2 | Obligations redaction/allowlist | Governance | S | REDACTED + deny blocked tools |  |  |
| US-G3 | Audit export | Governance | S | 100k rows ≤60s |  |  |

---

## 15) Checklists

### 15.1 MVP Readiness
- [ ] Model A deploy/invoke operational
- [ ] ATP v0 events ingested
- [ ] Trace explorer & logs correlation
- [ ] Cost per invocation & MTD aggregate
- [ ] OPA allow/deny wired in gateway
- [ ] Alerts to Slack (error/latency)
- [ ] Privacy: redaction verified
- [ ] Multi-tenant isolation verified

### 15.2 Launch Ops
- [ ] Runbooks: **RUNBOOK_local.md**
- [ ] OpenAPI synced (**openapi/api.yaml**)
- [ ] Sample agents (A/B) demo-ready
- [ ] Dashboards pre-configured
- [ ] Seed data for sandbox org

---

## 16) Appendices

### A. UI Information Architecture
- **Agents List** → **Agent Detail** (Overview, Invocations, Trace, Logs, Metrics, Policies, Audit)
- **Create Agent**: Toggle Model A vs Model B, SDK command surfaced when B chosen.
- **Badges**: **Verified Telemetry** (SDK) / **Partial Telemetry** (Proxy).

### B. Risks & Mitigations
- Partial telemetry without SDK → Badge + nudge.
- PII leakage → Obligations at ingestion + UI masking.
- Cost drift → Versioned adapters + reconciliation job.
- Trace volume → Success sampling; full failure traces.

### C. Glossary
- **ATP**: Agent Telemetry Protocol (our minimal schema for traces).
- **Invocation**: One execution of an agent entrypoint.
- **Step**: A logical unit within an invocation (prompt/tool/subagent/system).
- **Obligations**: Policy-mandated transforms (e.g., redact PII).
