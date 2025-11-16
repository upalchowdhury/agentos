-- db/schema.sql
-- AgentOS/AgentFlow unified core relational schema (PostgreSQL)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------
-- Tenants
------------------------------------------------------------
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    retention_days  INTEGER NOT NULL DEFAULT 30,
    status          TEXT NOT NULL DEFAULT 'active', -- active | suspended | deleted
    pii_config      JSONB,                          -- mirrors PIIConfig schema
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);

------------------------------------------------------------
-- Agents (logical agent catalog)
------------------------------------------------------------
CREATE TABLE agents (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name             TEXT NOT NULL,
    description      TEXT,
    platform         TEXT NOT NULL,        -- runtime | salesforce_agentforce | gcp_agent_engine | ...
    environment      TEXT NOT NULL DEFAULT 'production',
    team             TEXT,
    version          TEXT,
    runtime_type     TEXT NOT NULL DEFAULT 'external', -- native | external
    telemetry_badge  TEXT NOT NULL DEFAULT 'external', -- verified | partial | external
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_tenant_platform ON agents(tenant_id, platform);
CREATE INDEX idx_agents_tenant_team ON agents(tenant_id, team);

------------------------------------------------------------
-- Connectors
------------------------------------------------------------
CREATE TABLE connectors (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,  -- langchain, gcp_agent_engine, salesforce_agentforce, azure_copilot, generic_webhook
    name        TEXT NOT NULL,
    description TEXT,
    config      JSONB NOT NULL, -- secrets should be stored in vault; this is pointers/config only
    status      TEXT NOT NULL DEFAULT 'active', -- active | inactive | error
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_connectors_tenant_type ON connectors(tenant_id, type);

------------------------------------------------------------
-- Policy Bundles (OPA)
------------------------------------------------------------
CREATE TABLE policy_bundles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    rules       TEXT NOT NULL,           -- Rego or JSON, may be compressed/base64 in app layer
    version     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_policy_bundles_tenant_name ON policy_bundles(tenant_id, name);

------------------------------------------------------------
-- Alert Rules
------------------------------------------------------------
CREATE TABLE alert_rules (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    type        TEXT NOT NULL,           -- threshold | anomaly | compliance | availability
    expression  TEXT NOT NULL,           -- alert expression DSL
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    channels    TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[], -- email, slack, pagerduty, webhook
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_rules_tenant_type ON alert_rules(tenant_id, type);

------------------------------------------------------------
-- Alert Events
------------------------------------------------------------
CREATE TABLE alert_events (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    rule_id      UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    status       TEXT NOT NULL,          -- open | acknowledged | resolved
    message      TEXT,
    triggered_at TIMESTAMPTZ NOT NULL,
    resolved_at  TIMESTAMPTZ,
    context      JSONB,                  -- e.g. metric values, trace links
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_events_tenant_rule ON alert_events(tenant_id, rule_id);
CREATE INDEX idx_alert_events_triggered_at ON alert_events(triggered_at);

------------------------------------------------------------
-- Agent Executions (row-per-execution, denormalized for OLAP)
------------------------------------------------------------
CREATE TABLE agent_executions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    platform         TEXT NOT NULL,
    timestamp        TIMESTAMPTZ NOT NULL,
    agent_id         UUID,              -- FK to agents.id where possible
    agent_name       TEXT,
    agent_version    TEXT,
    agent_type       TEXT,
    trace_id         TEXT NOT NULL,
    span_id          TEXT NOT NULL,
    parent_span_id   TEXT,
    duration_ms      INTEGER,
    status           TEXT,              -- success | failure | timeout
    llm_provider     TEXT,
    llm_model        TEXT,
    input_tokens     INTEGER,
    output_tokens    INTEGER,
    total_cost_usd   NUMERIC(18, 8),
    input_sanitized  TEXT,
    output_sanitized TEXT,
    pii_detected     BOOLEAN,
    pii_types        TEXT[],
    user_id          TEXT,
    session_id       TEXT,
    environment      TEXT,
    team             TEXT,
    tags             JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_exec_tenant_time ON agent_executions(tenant_id, timestamp);
CREATE INDEX idx_agent_exec_trace ON agent_executions(trace_id);
CREATE INDEX idx_agent_exec_agent ON agent_executions(tenant_id, agent_id);

------------------------------------------------------------
-- Spans (for debugging / replay – this will often live in Tempo, but we may mirror keys here)
------------------------------------------------------------
CREATE TABLE spans (
    span_id            TEXT PRIMARY KEY,
    trace_id           TEXT NOT NULL,
    tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    parent_span_id     TEXT,
    name               TEXT NOT NULL,
    service_name       TEXT,
    kind               TEXT,
    attributes         JSONB,
    start_time         TIMESTAMPTZ NOT NULL,
    end_time           TIMESTAMPTZ NOT NULL,
    status             TEXT,
    status_message     TEXT,
    pii_detected       BOOLEAN,
    pii_types          TEXT[],
    redaction_applied  BOOLEAN,
    redaction_strategy TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_spans_tenant_trace ON spans(tenant_id, trace_id);
CREATE INDEX idx_spans_tenant_service ON spans(tenant_id, service_name);

------------------------------------------------------------
-- Edges (inter-span relationships)
------------------------------------------------------------
CREATE TABLE edges (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    trace_id     TEXT NOT NULL,
    from_span_id TEXT NOT NULL,
    to_span_id   TEXT NOT NULL,
    type         TEXT NOT NULL,          -- message | tool_call | dependency
    metadata     JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_edges_trace ON edges(trace_id);

------------------------------------------------------------
-- Cost Records
------------------------------------------------------------
CREATE TABLE cost_records (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    trace_id      TEXT,
    span_id       TEXT,
    agent_id      UUID,
    team          TEXT,
    platform      TEXT,
    provider      TEXT,
    model         TEXT,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    amount_usd    NUMERIC(18, 8) NOT NULL,
    currency      TEXT NOT NULL DEFAULT 'USD',
    timestamp     TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cost_tenant_time ON cost_records(tenant_id, timestamp);
CREATE INDEX idx_cost_tenant_agent ON cost_records(tenant_id, agent_id);

------------------------------------------------------------
-- Audit Events
------------------------------------------------------------
CREATE TABLE audit_events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    actor       TEXT NOT NULL,
    actor_type  TEXT NOT NULL, -- user | api_key | system
    action      TEXT NOT NULL,
    resource    TEXT,
    timestamp   TIMESTAMPTZ NOT NULL,
    details     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant_time ON audit_events(tenant_id, timestamp);

------------------------------------------------------------
-- Simple trigger to auto-update updated_at
------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tenants_updated
BEFORE UPDATE ON tenants
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_agents_updated
BEFORE UPDATE ON agents
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_connectors_updated
BEFORE UPDATE ON connectors
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_policy_bundles_updated
BEFORE UPDATE ON policy_bundles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_alert_rules_updated
BEFORE UPDATE ON alert_rules
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
