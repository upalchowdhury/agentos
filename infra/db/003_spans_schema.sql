-- Span-level telemetry schema (ATP v0.1)

CREATE TABLE IF NOT EXISTS telemetry_spans (
    span_id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    parent_span_id VARCHAR(64),
    invocation_id VARCHAR(64),
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL CHECK (kind IN ('prompt', 'tool', 'subagent', 'system', 'network')),
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'error', 'timeout', 'cancelled')),
    
    -- Agent info
    agent_id VARCHAR(255) NOT NULL,
    version_id VARCHAR(255),
    
    -- Model info
    model_provider VARCHAR(100),
    model_name VARCHAR(255),
    model_temperature FLOAT,
    model_top_p FLOAT,
    model_seed INTEGER,
    model_max_tokens INTEGER,
    
    -- IO tracking
    tokens_in INTEGER,
    tokens_out INTEGER,
    input_excerpt TEXT,
    output_excerpt TEXT,
    content_hash_in VARCHAR(64),
    content_hash_out VARCHAR(64),
    signature_verified BOOLEAN DEFAULT FALSE,
    
    -- Tool info
    tool_call_id VARCHAR(255),
    tool_name VARCHAR(255),
    tool_args_excerpt TEXT,
    tool_return_excerpt TEXT,
    
    -- Policy enforcement
    policy_enforced TEXT[],
    policy_obligations TEXT[],
    redaction_mask_ids TEXT[],
    budget_enforced_cents INTEGER,
    policy_allow BOOLEAN DEFAULT TRUE,
    
    -- Network info
    network_protocol VARCHAR(50),
    remote_agent_id VARCHAR(255),
    remote_version_id VARCHAR(255),
    request_id VARCHAR(255),
    edge_id VARCHAR(64),
    
    -- Error info
    error_type VARCHAR(255),
    error_message TEXT,
    
    -- Metadata
    metadata JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inter-agent edges
CREATE TABLE IF NOT EXISTS telemetry_edges (
    edge_id VARCHAR(64) PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    
    -- Source
    from_agent_id VARCHAR(255) NOT NULL,
    from_version_id VARCHAR(255),
    from_span_id VARCHAR(64),
    
    -- Destination
    to_agent_id VARCHAR(255) NOT NULL,
    to_version_id VARCHAR(255),
    to_span_id VARCHAR(64),
    
    -- Channel info
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('a2a', 'mcp', 'http', 'grpc', 'queue')),
    instruction_type VARCHAR(50) CHECK (instruction_type IN ('prompt', 'tool_request', 'system_directive', 'callback')),
    
    -- Content tracking
    size_bytes INTEGER,
    redaction_applied BOOLEAN DEFAULT FALSE,
    signature_verified BOOLEAN DEFAULT FALSE,
    content_hash VARCHAR(64),
    
    -- Metadata
    metadata JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for spans
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON telemetry_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_invocation_id ON telemetry_spans(invocation_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent ON telemetry_spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_agent ON telemetry_spans(agent_id, version_id, start_ts DESC);
CREATE INDEX IF NOT EXISTS idx_spans_kind ON telemetry_spans(kind);
CREATE INDEX IF NOT EXISTS idx_spans_status ON telemetry_spans(status);
CREATE INDEX IF NOT EXISTS idx_spans_edge ON telemetry_spans(edge_id);

-- Indexes for edges
CREATE INDEX IF NOT EXISTS idx_edges_time ON telemetry_edges(time DESC);
CREATE INDEX IF NOT EXISTS idx_edges_from_agent ON telemetry_edges(from_agent_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_edges_to_agent ON telemetry_edges(to_agent_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_edges_from_span ON telemetry_edges(from_span_id);
CREATE INDEX IF NOT EXISTS idx_edges_to_span ON telemetry_edges(to_span_id);
CREATE INDEX IF NOT EXISTS idx_edges_channel ON telemetry_edges(channel);

-- Foreign key references
ALTER TABLE telemetry_spans 
    ADD CONSTRAINT fk_spans_invocation 
    FOREIGN KEY (invocation_id) 
    REFERENCES invocations(invocation_id) 
    ON DELETE CASCADE;
