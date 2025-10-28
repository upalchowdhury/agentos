-- Enhanced Runtime Schema for Model A & Model B
-- Version: 0.2.0
-- Supports: Code upload, external registry, cost tracking, A2A

-- ============================================================================
-- AGENTS (Enhanced)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,  -- User/team DID
    model_type VARCHAR(1) NOT NULL CHECK (model_type IN ('A', 'B')),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    
    -- Model A specific
    runtime VARCHAR(20),  -- 'python3.11', 'python3.10', etc.
    image_ref VARCHAR(500),  -- Container image reference
    
    -- Model B specific
    endpoint_url VARCHAR(500),  -- External endpoint
    auth_config JSONB,  -- {type, value, header_name}
    rate_limit_config JSONB,  -- {rps, burst}
    health_status VARCHAR(20),  -- 'healthy', 'unhealthy', 'unknown'
    health_checked_at TIMESTAMP WITH TIME ZONE,
    
    -- Common metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT agents_model_a_fields CHECK (
        (model_type = 'A' AND runtime IS NOT NULL) OR
        (model_type = 'B' AND endpoint_url IS NOT NULL)
    )
);

-- Indexes for agents
CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner_id);
CREATE INDEX IF NOT EXISTS idx_agents_model_type ON agents(model_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);


-- ============================================================================
-- AGENT VERSIONS (Model A artifact history)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    
    -- Artifact info
    artifact_uri VARCHAR(500) NOT NULL,  -- S3/minio path
    artifact_checksum VARCHAR(64),  -- SHA256
    artifact_size_bytes BIGINT,
    
    -- Build info
    requirements_json JSONB DEFAULT '[]',  -- ['langchain', 'openai']
    env_json JSONB DEFAULT '{}',  -- {OPENAI_API_KEY: '***'}
    resources_json JSONB DEFAULT '{}',  -- {cpu: '500m', mem: '1Gi'}
    
    -- Container image
    image_ref VARCHAR(500),  -- Built image reference
    build_status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, IN_PROGRESS, SUCCESS, FAILED
    build_logs TEXT,
    build_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    built_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(agent_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_agent_versions_agent_id ON agent_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_versions_created_at ON agent_versions(created_at DESC);


-- ============================================================================
-- INVOCATIONS (Execution records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS invocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    
    -- Caller info
    requester_id VARCHAR(255) NOT NULL,  -- User or agent DID
    caller_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,  -- For A2A
    
    -- Input/Output
    input_hash VARCHAR(64),  -- SHA256 of input_data (for dedup)
    input_data JSONB,  -- Store input for audit/replay
    output_data JSONB,  -- Agent result
    error_message TEXT,
    
    -- Execution metrics
    status VARCHAR(20) NOT NULL,  -- SUCCESS, ERROR, TIMEOUT, DENIED
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INT,
    
    -- Cost tracking
    cost_decimal DECIMAL(10, 4),  -- Cost in USD
    cost_breakdown JSONB,  -- {compute: 0.001, llm_api: 0.002, tokens: 1500}
    
    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Provider info, model used, etc.
    
    CONSTRAINT invocations_execution_check CHECK (
        (status = 'SUCCESS' AND ended_at IS NOT NULL AND execution_time_ms IS NOT NULL) OR
        (status IN ('ERROR', 'TIMEOUT', 'DENIED'))
    )
);

-- Indexes for invocations
CREATE INDEX IF NOT EXISTS idx_invocations_agent_id ON invocations(agent_id);
CREATE INDEX IF NOT EXISTS idx_invocations_requester_id ON invocations(requester_id);
CREATE INDEX IF NOT EXISTS idx_invocations_caller_agent_id ON invocations(caller_agent_id);
CREATE INDEX IF NOT EXISTS idx_invocations_status ON invocations(status);
CREATE INDEX IF NOT EXISTS idx_invocations_started_at ON invocations(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_invocations_cost ON invocations(cost_decimal DESC);


-- ============================================================================
-- COST SNAPSHOTS (Aggregated billing data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cost_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    owner_id VARCHAR(255) NOT NULL,
    
    -- Time period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Aggregated metrics
    total_invocations INT NOT NULL DEFAULT 0,
    successful_invocations INT NOT NULL DEFAULT 0,
    failed_invocations INT NOT NULL DEFAULT 0,
    total_cost DECIMAL(10, 4) NOT NULL DEFAULT 0.0,
    
    -- Cost breakdown
    compute_cost DECIMAL(10, 4) DEFAULT 0.0,
    llm_api_cost DECIMAL(10, 4) DEFAULT 0.0,
    storage_cost DECIMAL(10, 4) DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(agent_id, period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_cost_snapshots_agent_id ON cost_snapshots(agent_id);
CREATE INDEX IF NOT EXISTS idx_cost_snapshots_owner_id ON cost_snapshots(owner_id);
CREATE INDEX IF NOT EXISTS idx_cost_snapshots_period ON cost_snapshots(period_start, period_end);


-- ============================================================================
-- AGENT TOKENS (For A2A authentication)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 of actual token
    
    -- Token metadata
    scopes TEXT[],  -- ['invoke:agent-b', 'read:agent-c']
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Security
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason TEXT,
    
    CONSTRAINT agent_tokens_expiry_check CHECK (expires_at > issued_at)
);

CREATE INDEX IF NOT EXISTS idx_agent_tokens_agent_id ON agent_tokens(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_tokens_hash ON agent_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_agent_tokens_expires ON agent_tokens(expires_at);


-- ============================================================================
-- ENHANCED AGENT STATS VIEW
-- ============================================================================
CREATE OR REPLACE VIEW agent_stats_v2 AS
SELECT 
    a.id as agent_id,
    a.name,
    a.owner_id,
    a.model_type,
    a.status,
    a.created_at,
    a.deployed_at,
    
    -- Invocation metrics
    COUNT(i.id) as total_invocations,
    COUNT(i.id) FILTER (WHERE i.status = 'SUCCESS') as successful_invocations,
    COUNT(i.id) FILTER (WHERE i.status = 'ERROR') as failed_invocations,
    COUNT(i.id) FILTER (WHERE i.status = 'TIMEOUT') as timeout_invocations,
    COUNT(i.id) FILTER (WHERE i.status = 'DENIED') as denied_invocations,
    
    -- Performance metrics
    AVG(i.execution_time_ms) FILTER (WHERE i.status = 'SUCCESS') as avg_execution_time_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY i.execution_time_ms) 
        FILTER (WHERE i.status = 'SUCCESS') as p50_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY i.execution_time_ms) 
        FILTER (WHERE i.status = 'SUCCESS') as p95_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY i.execution_time_ms) 
        FILTER (WHERE i.status = 'SUCCESS') as p99_latency_ms,
    
    -- Cost metrics
    SUM(i.cost_decimal) as total_cost_usd,
    AVG(i.cost_decimal) as avg_cost_per_invocation,
    
    -- Timestamps
    MAX(i.started_at) as last_invoked_at,
    NOW() - MAX(i.started_at) as time_since_last_invocation
    
FROM agents a
LEFT JOIN invocations i ON a.id = i.agent_id
GROUP BY a.id, a.name, a.owner_id, a.model_type, a.status, a.created_at, a.deployed_at;


-- ============================================================================
-- A2A INVOCATION GRAPH VIEW (for debugging agent chains)
-- ============================================================================
CREATE OR REPLACE VIEW a2a_invocation_graph AS
SELECT 
    i.id as invocation_id,
    i.agent_id as target_agent_id,
    a_target.name as target_agent_name,
    i.caller_agent_id as caller_agent_id,
    a_caller.name as caller_agent_name,
    i.requester_id,
    i.status,
    i.execution_time_ms,
    i.cost_decimal,
    i.started_at,
    i.ended_at
FROM invocations i
JOIN agents a_target ON i.agent_id = a_target.id
LEFT JOIN agents a_caller ON i.caller_agent_id = a_caller.id
WHERE i.caller_agent_id IS NOT NULL
ORDER BY i.started_at DESC;


-- ============================================================================
-- COST TRACKING FUNCTIONS
-- ============================================================================

-- Function to aggregate daily costs
CREATE OR REPLACE FUNCTION aggregate_daily_costs(p_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 day')
RETURNS void AS $$
BEGIN
    INSERT INTO cost_snapshots (
        agent_id,
        owner_id,
        period_start,
        period_end,
        total_invocations,
        successful_invocations,
        failed_invocations,
        total_cost,
        compute_cost,
        llm_api_cost
    )
    SELECT 
        a.id as agent_id,
        a.owner_id,
        p_date::timestamp,
        (p_date + INTERVAL '1 day')::timestamp,
        COUNT(i.id),
        COUNT(i.id) FILTER (WHERE i.status = 'SUCCESS'),
        COUNT(i.id) FILTER (WHERE i.status IN ('ERROR', 'TIMEOUT')),
        COALESCE(SUM(i.cost_decimal), 0.0),
        COALESCE(SUM((i.cost_breakdown->>'compute')::decimal), 0.0),
        COALESCE(SUM((i.cost_breakdown->>'llm_api')::decimal), 0.0)
    FROM agents a
    LEFT JOIN invocations i ON a.id = i.agent_id 
        AND DATE(i.started_at) = p_date
    GROUP BY a.id, a.owner_id
    ON CONFLICT (agent_id, period_start, period_end) 
    DO UPDATE SET
        total_invocations = EXCLUDED.total_invocations,
        successful_invocations = EXCLUDED.successful_invocations,
        failed_invocations = EXCLUDED.failed_invocations,
        total_cost = EXCLUDED.total_cost,
        compute_cost = EXCLUDED.compute_cost,
        llm_api_cost = EXCLUDED.llm_api_cost;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- SEED DATA (default values)
-- ============================================================================

-- Insert default cost pricing (for reference, actual calc in app)
CREATE TABLE IF NOT EXISTS pricing_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'gemini', 'compute'
    model VARCHAR(100),  -- 'gpt-4', 'claude-3', null for compute
    unit VARCHAR(20) NOT NULL,  -- 'token', 'second', 'mb'
    price_per_unit DECIMAL(12, 8) NOT NULL,
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_until TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Insert sample pricing
INSERT INTO pricing_config (provider, model, unit, price_per_unit, metadata) VALUES
    ('openai', 'gpt-4', 'token', 0.00003, '{"input": 0.00003, "output": 0.00006}'::jsonb),
    ('anthropic', 'claude-3-opus', 'token', 0.000015, '{"input": 0.000015, "output": 0.000075}'::jsonb),
    ('gemini', 'gemini-pro', 'token', 0.0000005, '{"input": 0.0000005, "output": 0.0000015}'::jsonb),
    ('compute', null, 'cpu_second', 0.00001, '{}'::jsonb),
    ('compute', null, 'memory_mb_second', 0.000001, '{}'::jsonb)
ON CONFLICT DO NOTHING;


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update agents.updated_at on change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- GRANTS (adjust for your role names)
-- ============================================================================

-- Grant permissions to runtime service
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO runtime_service;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO runtime_service;

-- Grant read-only to observability service
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO observability_service;
