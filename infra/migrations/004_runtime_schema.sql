-- Runtime Service Schema Migration
-- Creates tables for agent deployments, invocations, and metrics

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Deployments Table
CREATE TABLE IF NOT EXISTS agent_deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_did VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('DEPLOYING', 'RUNNING', 'STOPPED', 'FAILED', 'TERMINATED')),
    container_id VARCHAR(255) NULL,
    code TEXT NOT NULL,
    code_hash BIGINT NOT NULL,
    resource_limits JSONB NOT NULL,
    deployed_at TIMESTAMPTZ DEFAULT NOW(),
    stopped_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Agent Invocations Table
CREATE TABLE IF NOT EXISTS agent_invocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_did VARCHAR(255) NOT NULL,
    deployment_id UUID NOT NULL REFERENCES agent_deployments(id) ON DELETE CASCADE,
    input_hash VARCHAR(64) NULL,
    output_hash VARCHAR(64) NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('SUCCESS', 'ERROR', 'TIMEOUT')),
    execution_time_ms INTEGER NOT NULL,
    cost_cents INTEGER DEFAULT 0,
    invoked_at TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT NULL
);

-- Agent Metrics Table
CREATE TABLE IF NOT EXISTS agent_metrics (
    agent_did VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    cpu_percent FLOAT,
    memory_mb INTEGER,
    network_rx_bytes BIGINT,
    network_tx_bytes BIGINT,
    active_connections INTEGER,
    PRIMARY KEY (agent_did, timestamp)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_deployments_agent ON agent_deployments(agent_did);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON agent_deployments(status);
CREATE INDEX IF NOT EXISTS idx_invocations_agent_time ON agent_invocations(agent_did, invoked_at DESC);
CREATE INDEX IF NOT EXISTS idx_invocations_deployment ON agent_invocations(deployment_id);
CREATE INDEX IF NOT EXISTS idx_metrics_time ON agent_metrics(timestamp DESC);

-- Agent Stats View
CREATE OR REPLACE VIEW agent_stats AS
SELECT 
    d.agent_did,
    d.status,
    d.deployed_at,
    COUNT(i.id) as total_invocations,
    MAX(i.invoked_at) as last_invoked_at,
    SUM(i.cost_cents) as total_cost_cents,
    AVG(i.execution_time_ms) as avg_execution_time_ms
FROM agent_deployments d
LEFT JOIN agent_invocations i ON d.id = i.deployment_id
GROUP BY d.agent_did, d.status, d.deployed_at;

-- Comments for documentation
COMMENT ON TABLE agent_deployments IS 'Stores agent deployment information and code';
COMMENT ON TABLE agent_invocations IS 'Records all agent invocations and their results';
COMMENT ON TABLE agent_metrics IS 'Time-series metrics for agent resource usage';
COMMENT ON VIEW agent_stats IS 'Aggregated statistics per agent';
