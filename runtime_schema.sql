-- Runtime service tables
CREATE TABLE IF NOT EXISTS agent_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    requirements JSONB DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_deployments_agent_id ON agent_deployments(agent_id);
CREATE INDEX IF NOT EXISTS idx_deployments_created ON agent_deployments(created_at);

CREATE TABLE IF NOT EXISTS agent_invocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    input JSONB NOT NULL,
    output JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invocations_agent_id ON agent_invocations(agent_id);
CREATE INDEX IF NOT EXISTS idx_invocations_created ON agent_invocations(created_at);
