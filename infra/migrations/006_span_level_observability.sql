-- ============================================================================
-- Span-Level Observability Schema (ATP v0.1)
-- ============================================================================
-- Adds fine-grained span and edge tracking for multi-agent flows
-- Enables flamegraph visualization, inter-agent sequence diagrams,
-- span-level replay, and anomaly detection
--
-- Version: 0.3.0
-- References: ATP v0.1 spec from AgentOS_Span_Debug_Addendum.md
-- ============================================================================

-- ============================================================================
-- TELEMETRY SPANS (First-class span entities)
-- ============================================================================
CREATE TABLE IF NOT EXISTS telemetry_spans (
    -- Identity
    span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL,
    parent_span_id UUID REFERENCES telemetry_spans(span_id) ON DELETE CASCADE,

    -- Relationships
    invocation_id UUID NOT NULL REFERENCES invocations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,

    -- Span metadata
    name VARCHAR(200) NOT NULL,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('prompt', 'tool', 'subagent', 'system', 'network')),
    start_ts TIMESTAMP WITH TIME ZONE NOT NULL,
    end_ts TIMESTAMP WITH TIME ZONE,
    duration_ms INT,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error', 'timeout', 'cancelled', 'running')),

    -- Model information (for prompt spans)
    model_provider VARCHAR(50),  -- 'openai', 'anthropic', 'vertex', 'bedrock'
    model_name VARCHAR(100),     -- 'gpt-4o', 'claude-3-opus', etc.
    model_params JSONB,          -- {temperature, top_p, seed, max_tokens}

    -- I/O tracking
    tokens_in INT,
    tokens_out INT,
    input_excerpt TEXT,          -- Redacted excerpt (max 2048 chars)
    output_excerpt TEXT,         -- Redacted excerpt (max 2048 chars)
    content_hash_in VARCHAR(64), -- SHA256 of input
    content_hash_out VARCHAR(64), -- SHA256 of output
    signature_verified BOOLEAN DEFAULT FALSE,

    -- Tool information (for tool spans)
    tool_call_id VARCHAR(100),
    tool_name VARCHAR(200),
    tool_args_excerpt TEXT,      -- Redacted
    tool_return_excerpt TEXT,    -- Redacted

    -- Policy & governance
    policy_enforced TEXT[],      -- Policy IDs applied
    obligations TEXT[],          -- Redaction, allowlist, budget
    redaction_mask_ids TEXT[],   -- Mask IDs applied
    budget_enforced_cents INT,
    policy_allow BOOLEAN DEFAULT TRUE,

    -- Network information (for subagent/network spans)
    protocol VARCHAR(20),        -- 'a2a', 'mcp', 'http', 'grpc', 'none'
    remote_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    remote_version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    request_id VARCHAR(100),
    edge_id UUID,                -- FK to telemetry_edges

    -- Cost tracking
    cost_cents INT DEFAULT 0,

    -- Error information
    error_type VARCHAR(100),
    error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_trace_id ON telemetry_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_invocation_id ON telemetry_spans(invocation_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_agent_id ON telemetry_spans(agent_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_parent_span_id ON telemetry_spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_start_ts ON telemetry_spans(start_ts DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_kind ON telemetry_spans(kind);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_status ON telemetry_spans(status);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_remote_agent_id ON telemetry_spans(remote_agent_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_edge_id ON telemetry_spans(edge_id);

-- GIN index for policy arrays
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_policy_gin ON telemetry_spans USING GIN(policy_enforced);


-- ============================================================================
-- TELEMETRY EDGES (Inter-agent communication tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS telemetry_edges (
    -- Identity
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL,

    -- Source (caller)
    from_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    from_version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    from_span_id UUID REFERENCES telemetry_spans(span_id) ON DELETE CASCADE,

    -- Target (callee)
    to_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    to_version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    to_span_id UUID REFERENCES telemetry_spans(span_id) ON DELETE CASCADE,

    -- Communication metadata
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('a2a', 'mcp', 'http', 'grpc', 'queue')),
    instruction_type VARCHAR(50) NOT NULL CHECK (instruction_type IN ('prompt', 'tool_request', 'system_directive', 'callback', 'response')),

    -- Content tracking
    size_bytes INT,
    content_hash VARCHAR(64),    -- SHA256 of message payload
    redaction_applied BOOLEAN DEFAULT FALSE,
    signature_verified BOOLEAN DEFAULT FALSE,

    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    latency_ms INT,              -- Edge traversal latency

    -- Policy
    policy_enforced TEXT[],
    obligations TEXT[],

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for edge queries
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_trace_id ON telemetry_edges(trace_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_from_agent ON telemetry_edges(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_to_agent ON telemetry_edges(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_from_span ON telemetry_edges(from_span_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_to_span ON telemetry_edges(to_span_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_timestamp ON telemetry_edges(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_edges_channel ON telemetry_edges(channel);


-- ============================================================================
-- SPAN LINKS (OTel-compatible causal relationships)
-- ============================================================================
CREATE TABLE IF NOT EXISTS span_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    span_id UUID NOT NULL REFERENCES telemetry_spans(span_id) ON DELETE CASCADE,
    linked_span_id UUID NOT NULL REFERENCES telemetry_spans(span_id) ON DELETE CASCADE,
    link_type VARCHAR(30) NOT NULL CHECK (link_type IN ('follows_from', 'caused_by', 'responds_to', 'child_of')),
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(span_id, linked_span_id, link_type)
);

CREATE INDEX IF NOT EXISTS idx_span_links_span_id ON span_links(span_id);
CREATE INDEX IF NOT EXISTS idx_span_links_linked_span_id ON span_links(linked_span_id);


-- ============================================================================
-- SPAN ANOMALIES (Security & quality detection)
-- ============================================================================
CREATE TABLE IF NOT EXISTS span_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    span_id UUID NOT NULL REFERENCES telemetry_spans(span_id) ON DELETE CASCADE,
    trace_id UUID NOT NULL,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    -- Anomaly classification
    anomaly_type VARCHAR(50) NOT NULL CHECK (anomaly_type IN (
        'prompt_injection',
        'tool_abuse',
        'context_tampering',
        'cost_outlier',
        'latency_outlier',
        'signature_mismatch',
        'policy_violation',
        'unusual_behavior'
    )),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence DECIMAL(3, 2) CHECK (confidence >= 0 AND confidence <= 1),  -- 0.00 to 1.00

    -- Detection details
    detector_name VARCHAR(100) NOT NULL,  -- 'regex_injection', 'ml_classifier', 'statistical_outlier'
    detector_version VARCHAR(20),
    evidence JSONB,  -- Detector-specific evidence

    -- Status
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'investigating', 'resolved', 'false_positive')),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    resolution_notes TEXT,

    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_span_anomalies_span_id ON span_anomalies(span_id);
CREATE INDEX IF NOT EXISTS idx_span_anomalies_trace_id ON span_anomalies(trace_id);
CREATE INDEX IF NOT EXISTS idx_span_anomalies_agent_id ON span_anomalies(agent_id);
CREATE INDEX IF NOT EXISTS idx_span_anomalies_type ON span_anomalies(anomaly_type);
CREATE INDEX IF NOT EXISTS idx_span_anomalies_severity ON span_anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_span_anomalies_status ON span_anomalies(status);
CREATE INDEX IF NOT EXISTS idx_span_anomalies_detected_at ON span_anomalies(detected_at DESC);


-- ============================================================================
-- TRACE CONTEXT (W3C traceparent/tracestate baggage)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trace_context (
    trace_id UUID PRIMARY KEY,
    traceparent VARCHAR(55) NOT NULL,  -- W3C format: 00-{trace_id}-{span_id}-{flags}
    tracestate TEXT,                    -- Vendor-specific key-value pairs

    -- Baggage (cross-cutting concerns)
    baggage JSONB DEFAULT '{}',  -- {agent_id, version_id, tenant_id, run_mode, budget_remaining_cents}

    -- Run configuration (for deterministic replay)
    run_mode VARCHAR(20) DEFAULT 'normal' CHECK (run_mode IN ('normal', 'deterministic')),
    config_hash VARCHAR(64),  -- Hash of model+params+tools+env+policies

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trace_context_config_hash ON trace_context(config_hash);


-- ============================================================================
-- VIEWS FOR SPAN ANALYTICS
-- ============================================================================

-- Span tree view (hierarchical spans for flamegraph)
CREATE OR REPLACE VIEW span_tree AS
WITH RECURSIVE span_hierarchy AS (
    -- Root spans (no parent)
    SELECT
        s.span_id,
        s.trace_id,
        s.parent_span_id,
        s.name,
        s.kind,
        s.start_ts,
        s.duration_ms,
        s.status,
        s.agent_id,
        0 AS depth,
        ARRAY[s.span_id] AS path
    FROM telemetry_spans s
    WHERE s.parent_span_id IS NULL

    UNION ALL

    -- Child spans
    SELECT
        s.span_id,
        s.trace_id,
        s.parent_span_id,
        s.name,
        s.kind,
        s.start_ts,
        s.duration_ms,
        s.status,
        s.agent_id,
        h.depth + 1,
        h.path || s.span_id
    FROM telemetry_spans s
    INNER JOIN span_hierarchy h ON s.parent_span_id = h.span_id
)
SELECT * FROM span_hierarchy
ORDER BY path;


-- Inter-agent flow view (sequence diagram data)
CREATE OR REPLACE VIEW inter_agent_flows AS
SELECT
    e.edge_id,
    e.trace_id,
    e.timestamp,
    e.channel,
    e.instruction_type,

    -- Source agent
    a_from.name as from_agent_name,
    e.from_agent_id,
    e.from_version_id,
    s_from.name as from_span_name,
    s_from.kind as from_span_kind,

    -- Target agent
    a_to.name as to_agent_name,
    e.to_agent_id,
    e.to_version_id,
    s_to.name as to_span_name,
    s_to.kind as to_span_kind,

    -- Metrics
    e.latency_ms,
    e.size_bytes,
    e.signature_verified,
    e.redaction_applied,

    -- Policy
    e.policy_enforced,
    e.obligations

FROM telemetry_edges e
JOIN agents a_from ON e.from_agent_id = a_from.id
JOIN agents a_to ON e.to_agent_id = a_to.id
JOIN telemetry_spans s_from ON e.from_span_id = s_from.span_id
JOIN telemetry_spans s_to ON e.to_span_id = s_to.span_id
ORDER BY e.timestamp ASC;


-- Span statistics per agent
CREATE OR REPLACE VIEW span_stats_per_agent AS
SELECT
    s.agent_id,
    a.name as agent_name,
    s.kind,
    COUNT(*) as span_count,
    AVG(s.duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY s.duration_ms) as p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY s.duration_ms) as p95_duration_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY s.duration_ms) as p99_duration_ms,
    SUM(s.cost_cents) as total_cost_cents,
    COUNT(*) FILTER (WHERE s.status = 'error') as error_count,
    COUNT(*) FILTER (WHERE s.policy_allow = FALSE) as policy_denied_count
FROM telemetry_spans s
JOIN agents a ON s.agent_id = a.id
GROUP BY s.agent_id, a.name, s.kind;


-- Anomaly summary per agent
CREATE OR REPLACE VIEW anomaly_summary AS
SELECT
    a.agent_id,
    ag.name as agent_name,
    a.anomaly_type,
    a.severity,
    COUNT(*) as anomaly_count,
    COUNT(*) FILTER (WHERE a.status = 'open') as open_count,
    COUNT(*) FILTER (WHERE a.status = 'resolved') as resolved_count,
    MAX(a.detected_at) as last_detected_at
FROM span_anomalies a
JOIN agents ag ON a.agent_id = ag.id
GROUP BY a.agent_id, ag.name, a.anomaly_type, a.severity;


-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to calculate span depth in tree
CREATE OR REPLACE FUNCTION get_span_depth(p_span_id UUID)
RETURNS INT AS $$
DECLARE
    v_depth INT := 0;
    v_current_span_id UUID := p_span_id;
    v_parent_span_id UUID;
BEGIN
    LOOP
        SELECT parent_span_id INTO v_parent_span_id
        FROM telemetry_spans
        WHERE span_id = v_current_span_id;

        EXIT WHEN v_parent_span_id IS NULL;

        v_depth := v_depth + 1;
        v_current_span_id := v_parent_span_id;

        -- Safety: prevent infinite loops
        IF v_depth > 100 THEN
            RAISE EXCEPTION 'Span depth exceeds maximum (possible cycle)';
        END IF;
    END LOOP;

    RETURN v_depth;
END;
$$ LANGUAGE plpgsql;


-- Function to get all spans in a trace
CREATE OR REPLACE FUNCTION get_trace_spans(p_trace_id UUID)
RETURNS TABLE (
    span_id UUID,
    parent_span_id UUID,
    name VARCHAR,
    kind VARCHAR,
    start_ts TIMESTAMP WITH TIME ZONE,
    duration_ms INT,
    status VARCHAR,
    depth INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.span_id,
        s.parent_span_id,
        s.name,
        s.kind,
        s.start_ts,
        s.duration_ms,
        s.status,
        get_span_depth(s.span_id) as depth
    FROM telemetry_spans s
    WHERE s.trace_id = p_trace_id
    ORDER BY s.start_ts ASC;
END;
$$ LANGUAGE plpgsql;


-- Function to detect cost outliers
CREATE OR REPLACE FUNCTION detect_cost_outliers(
    p_agent_id UUID,
    p_threshold_std_devs DECIMAL DEFAULT 3.0
)
RETURNS TABLE (
    span_id UUID,
    cost_cents INT,
    avg_cost DECIMAL,
    std_dev DECIMAL,
    z_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH stats AS (
        SELECT
            AVG(s.cost_cents) as mean_cost,
            STDDEV(s.cost_cents) as std_cost
        FROM telemetry_spans s
        WHERE s.agent_id = p_agent_id
          AND s.cost_cents > 0
    )
    SELECT
        s.span_id,
        s.cost_cents,
        st.mean_cost,
        st.std_cost,
        (s.cost_cents - st.mean_cost) / NULLIF(st.std_cost, 0) as z_score
    FROM telemetry_spans s
    CROSS JOIN stats st
    WHERE s.agent_id = p_agent_id
      AND s.cost_cents > 0
      AND ABS((s.cost_cents - st.mean_cost) / NULLIF(st.std_cost, 0)) > p_threshold_std_devs
    ORDER BY z_score DESC;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-calculate span duration on end
CREATE OR REPLACE FUNCTION calculate_span_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_ts IS NOT NULL AND NEW.start_ts IS NOT NULL THEN
        NEW.duration_ms = EXTRACT(EPOCH FROM (NEW.end_ts - NEW.start_ts)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_span_duration
    BEFORE INSERT OR UPDATE ON telemetry_spans
    FOR EACH ROW
    EXECUTE FUNCTION calculate_span_duration();


-- Update trace_context updated_at
CREATE TRIGGER update_trace_context_updated_at
    BEFORE UPDATE ON trace_context
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- GRANTS (adjust for your role names)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON telemetry_spans TO runtime_service;
-- GRANT SELECT, INSERT, UPDATE ON telemetry_edges TO runtime_service;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO observability_service;


-- ============================================================================
-- COMPLETION
-- ============================================================================
-- Migration 006: Span-Level Observability ✓
-- Enables: Flamegraph, sequence diagrams, span replay, anomaly detection
-- Next: Implement span instrumentation in runtime executor
-- ============================================================================
