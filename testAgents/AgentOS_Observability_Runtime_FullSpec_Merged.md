# AgentOS — Unified Observability & Runtime PRD + Developer Workbook
(Full main content from previous spec)


---

# Addendum: Span-Level Mapping & Inter‑Agent Debugging (ATP v0.1)
_Last updated: 2025-11-02 12:45 ET_

This addendum extends the **AgentOS — Unified Observability & Runtime PRD + Developer Workbook** to introduce **lowest‑level span mapping**, **inter‑agent prompt/instruction flow debugging**, and **deterministic replay hooks**. It is Windsurf/Claude‑Code ready. You can paste this into the end of your main spec or keep as `docs/product/AgentOS_Span_Debug_Addendum.md`.

---

## A1. Objectives
1) Capture **span‑level telemetry** across prompts, tools, sub‑agents, and network boundaries.  
2) Build a **causal graph** of messages/instructions flowing **between agents** (A2A/MCP/HTTP/gRPC).  
3) Provide **deterministic replay** for any span/edge with stable configs (seed/model/tools).  
4) Detect prompt injection, tool abuse, and context‑tampering at **span granularity**.

---

## A2. Standards & Propagation
- **Trace context:** W3C `traceparent`, `tracestate`; **causal links** via OTel Span Links.
- **Baggage:** `agent_id`, `version_id`, `policy_ids`, `tenant_id`, `run_mode` (deterministic|normal), `budget_remaining_cents`.
- **Cross‑agent edges:** Include **Edge IDs** and **Message IDs** for A→B handoff (A2A/MCP).

---

## A3. Schema Extensions — ATP v0.1
> Extends §9 “Telemetry Schema — ATP v0 (Extended)” of the main spec.

```yaml
trace:
  # ...existing fields...
  run_mode: deterministic|normal
  # Hash the full effective config to enable deterministic replay identity:
  config_hash: string              # hash(model+params+tools+env+policy bundle)

spans:
  - span_id: string
    parent_span_id: string|null
    name: string
    kind: prompt|tool|subagent|system|network
    start_ts: RFC3339
    end_ts: RFC3339
    duration_ms: int
    status: success|error|timeout|cancelled
    agent:
      agent_id: string
      version_id: string
    model:
      provider: string?            # openai|anthropic|vertex|bedrock|custom
      name: string?                # gpt-4o, sonnet, etc.
      parameters:
        temperature: float?
        top_p: float?
        seed: int?
        max_tokens: int?
    io:
      tokens_in: int?
      tokens_out: int?
      input_excerpt: string?       # redacted
      output_excerpt: string?      # redacted
      content_hash_in: string?
      content_hash_out: string?
      signature_verified: bool?
    tool:
      call_id: string?
      name: string?
      args_excerpt: string?
      return_excerpt: string?
    policy:
      policy_enforced: [string]    # policy IDs applied
      obligations: [string]        # redact/allowlist/budget
      redaction_mask_ids: [string] # ids of masks applied to excerpts
      budget_enforced_cents: int?
      allow: bool
    network:
      protocol: a2a|mcp|http|grpc|none
      remote_agent_id: string?     # if subagent call
      remote_version_id: string?
      request_id: string?
      edge_id: string?             # causal edge between agents
    links:
      - type: follows_from|caused_by|responds_to
        span_id: string            # OTel span link target
```

**Edge entity (new, persisted separately for inter‑agent visualization):**
```yaml
edge:
  edge_id: string
  time: RFC3339
  from_agent_id: string
  from_version_id: string
  from_span_id: string
  to_agent_id: string
  to_version_id: string
  to_span_id: string
  channel: a2a|mcp|http|grpc|queue
  instruction_type: prompt|tool_request|system_directive|callback
  size_bytes: int
  redaction_applied: bool
  signature_verified: bool
  content_hash: string
```

---

## A4. Detection & Diagnostics (Span‑Level)
- **Injection heuristics:** regex + ML classifiers on input excerpts (post‑redaction); features include unusual directive verbs, jailbreak tokens, tool‑use redirections.
- **Tool‑abuse detection:** mismatch between tool contract and args schema; repeated retries; high latency deltas.
- **Context‑tampering:** hash mismatch (`content_hash_in`) against signed parent message; **signature_verified=false** hot path alerts.
- **Cost anomalies:** step cost sigma‑outlier per agent/version.
- **Side‑effects guard:** policy obligations (allowlist) block unapproved domains; span flagged when attempted.

---

## A5. UI Additions
1) **Span Flamegraph:** hierarchical spans; select to view model/tool/policy panes.  
2) **Inter‑Agent Sequence Diagram:** live causal edges (A→B→C) with protocol badges and signature status.  
3) **Edge Inspector Drawer:** shows input/output excerpts (masked), hashes, signatures, and policy/obligation history.  
4) **Deterministic Replay Button** on any span or edge → prefilled “Replay Run” modal with config snapshot.  
5) **Risk Overlays:** injection score, policy violations, cost outliers.

---

## A6. SDK & Sidecar Instrumentation
- **SDK interceptors:** LangChain/LangGraph, CrewAI, AutoGen; MCP server middleware; A2A client wrappers. Capture span start/stop, hashes, model params, tool calls.  
- **HTTP/gRPC middleware:** propagate `traceparent` + baggage; sign payloads for **signature_verified** checks.  
- **Envoy/Flex sidecar:** WASM filter to inject/propagate headers, generate **network spans**, compute `content_hash`, attach `edge_id`, and emit ATP v0.1 to collector.

---

## A7. Deterministic Replay
- **Config capture:** model + parameters + tool binaries/versions + prompts + seeds + policies → `config_hash`.  
- **Replay API:** `POST /api/replay/:span_id` or `/api/replay/edge/:edge_id` with snapshot pointer.  
- **Nondeterminism detector:** compare hashes; mark external I/O and clock/file/network randomness as **unfrozen** contributors.

---

## A8. New User Stories
- **US-O5 (M) Span Flamegraph & Inspector**  
  **As** a developer **I want** span‑level flamegraph **so that** I can pinpoint slow or failing spans.  
  **AC:** Expand node shows model/tool/policy panes; links to logs by `span_id`.

- **US-O6 (M) Inter‑Agent Sequence View**  
  **As** an SRE **I want** a sequence diagram of A→B→C hops **so that** I can debug cross‑agent flows.  
  **AC:** Shows channel, signature status, edge latency, size; click → Edge Inspector.

- **US-O7 (S) Span Anomaly Detection**  
  **As** Security **I want** injection/tool‑abuse/context‑tampering scores **so that** I can triage risks.  
  **AC:** Alerts on thresholds; deep link to span/edge.

- **US-D2 (M) Span/Edge Replay**  
  **As** a developer **I want** to replay any span or edge **so that** I can reproduce bugs deterministically.  
  **AC:** Replay uses `config_hash`; mismatches flagged.

---

## A9. API & Storage
**APIs (add):**
- `GET /api/spans/:span_id`  
- `GET /api/spans?trace_id=` (with pagination)  
- `GET /api/edges?trace_id=` / `GET /api/edges/:edge_id`  
- `POST /api/replay/:span_id` / `POST /api/replay/edge/:edge_id`

**Tables (add/extend):**
- `telemetry_spans(...)` — from A3.  
- `telemetry_edges(...)` — from A3.  
- Indexes: `(trace_id)`, `(span_id)`, `(edge_id)`, `(agent_id, version_id, start_ts)`.

---

## A10. Acceptance Tests
1) **Span Integrity:** create nested prompt→tool spans; validate parent/child and durations.  
2) **Edge Propagation:** A2A call A→B emits edge with signature_verified=true; baggage carried.  
3) **Injection Alert:** crafted jailbreak triggers span anomaly alert.  
4) **Replay Parity:** replay `span_id` reproduces outputs; `config_hash` unchanged.  
5) **Sidecar Headers:** Envoy/Flex deployment preserves `traceparent` and emits network spans.

---

## A11. KPIs (additions)
- **Span coverage:** ≥ 95% prompts/tools wrapped by spans.  
- **Edge fidelity:** ≥ 99% cross‑agent edges captured with valid `edge_id`.  
- **Replay success:** ≥ 90% spans replay to identical outputs (deterministic mode).  
- **Anomaly MTTR:** < 10 minutes from alert to responsible span identification.

---

## A12. Developer Tasks (Windsurf/Claude Code)
- Create `services/observability/ingest/spans_api.py` and `edges_api.py`.  
- Add `telemetry_spans` and `telemetry_edges` migrations + indexes.  
- Implement **SDK interceptors** for LangChain/LangGraph + wrappers for MCP/A2A.  
- Implement **Envoy WASM filter** (Rust/AssemblyScript) for header propagation + edge emission.  
- Build **Flamegraph**, **Sequence View**, and **Edge Inspector** components in `web-ui`.  
- Implement **Replay service** (reads config snapshot → executes in deterministic mode).  
- Add **anomaly detectors** with pluggable rules (`services/observability/anomaly/`).  
- Extend **ATP→OTel bridge** to emit span links and edge attributes.

---

## A13. Security & Privacy
- Excerpts are **post‑redaction**; masks carry `redaction_mask_ids`.  
- Hashes/signatures computed on **masked content** to avoid sensitive leakage.  
- Baggage minimized; PII never placed in headers; signatures cover canonicalized payload.

---

## A14. Sample SDK Pseudocode (Python)
```python
from contextlib import contextmanager
from agentos.sdk import telemetry, hashing, policy

@contextmanager
def span(name, kind, agent_id, version_id, links=None):
    span_id = telemetry.start_span(name=name, kind=kind, agent_id=agent_id,
                                   version_id=version_id, links=links)
    try:
        yield span_id
        telemetry.end_span(span_id, status="success")
    except Exception as e:
        telemetry.end_span(span_id, status="error", error_type=type(e).__name__, error_message=str(e))
        raise

def call_model(prompt, model_cfg):
    with span("model_infer", "prompt", agent_id=AGENT_ID, version_id=VERSION, links=telemetry.current_links()) as sid:
        inp = redact(prompt)
        h_in = hashing.hash(inp)
        out = llm_call(prompt=prompt, **model_cfg)
        h_out = hashing.hash(mask(out))
        telemetry.annotate_span(sid, io={ "input_excerpt": mask(inp)[:512], "output_excerpt": mask(out)[:512],
                                          "content_hash_in": h_in, "content_hash_out": h_out },
                                model={"provider": model_cfg["provider"], "name": model_cfg["name"], "parameters": model_cfg})
        return out
```
