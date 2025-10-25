-- Agent Economy OS - Initial Database Schema

-- DIDs table
CREATE TABLE IF NOT EXISTS dids (
    id VARCHAR(255) PRIMARY KEY,
    document JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dids_created ON dids(created_at);

-- Credentials table
CREATE TABLE IF NOT EXISTS credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_did VARCHAR(255) NOT NULL,
    jwt TEXT NOT NULL,
    issued_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credentials_subject ON credentials(subject_did);
CREATE INDEX IF NOT EXISTS idx_credentials_expires ON credentials(expires_at);
CREATE INDEX IF NOT EXISTS idx_credentials_jwt ON credentials(jwt);

-- Interactions table (audit log)
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caller_did VARCHAR(255) NOT NULL,
    target_did VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interactions_caller ON interactions(caller_did, created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_target ON interactions(target_did, created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_conversation ON interactions(conversation_id, created_at);

-- Memories table
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_did, created_at);
CREATE INDEX IF NOT EXISTS idx_memories_conversation ON memories(conversation_id, created_at);

-- Tenant access control
CREATE TABLE IF NOT EXISTS tenant_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    permission VARCHAR(50) NOT NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tenant_access_unique 
    ON tenant_access(agent_did, resource_type, resource_id, permission);

-- Cost tracking
CREATE TABLE IF NOT EXISTS cost_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    cost_cents INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cost_events_agent ON cost_events(agent_did, created_at);
CREATE INDEX IF NOT EXISTS idx_cost_events_type ON cost_events(event_type, created_at);

-- Add update trigger for dids
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_dids_updated_at BEFORE UPDATE ON dids
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
