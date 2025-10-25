-- RBAC/ABAC Schema Extension
-- Version: 0.1.0

-- Roles
CREATE TABLE IF NOT EXISTS roles (
    name VARCHAR(50) PRIMARY KEY,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Permissions
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) REFERENCES roles(name) ON DELETE CASCADE,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    constraints JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Roles (many-to-many)
CREATE TABLE IF NOT EXISTS agent_roles (
    agent_did VARCHAR(255) REFERENCES dids(id) ON DELETE CASCADE,
    role_name VARCHAR(50) REFERENCES roles(name) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (agent_did, role_name)
);

-- Content Policy Violations
CREATE TABLE IF NOT EXISTS content_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL REFERENCES dids(id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_permissions_role ON permissions(role_name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource, action);
CREATE INDEX IF NOT EXISTS idx_agent_roles_agent_did ON agent_roles(agent_did);
CREATE INDEX IF NOT EXISTS idx_agent_roles_role_name ON agent_roles(role_name);
CREATE INDEX IF NOT EXISTS idx_content_violations_agent_did ON content_violations(agent_did);
CREATE INDEX IF NOT EXISTS idx_content_violations_type ON content_violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_content_violations_created_at ON content_violations(created_at);

-- Default roles
INSERT INTO roles (name, description) VALUES
    ('agent:basic', 'Basic agent with read-only access'),
    ('agent:executor', 'Can execute tasks and write memory'),
    ('agent:orchestrator', 'Can invoke other agents and manage workflows'),
    ('agent:admin', 'Full administrative access')
ON CONFLICT (name) DO NOTHING;

-- Default permissions for basic role
INSERT INTO permissions (role_name, resource, action) VALUES
    ('agent:basic', 'memory:read', 'read'),
    ('agent:basic', 'agent:info', 'read')
ON CONFLICT DO NOTHING;

-- Default permissions for executor role
INSERT INTO permissions (role_name, resource, action) VALUES
    ('agent:executor', 'memory:read', 'read'),
    ('agent:executor', 'memory:write', 'write'),
    ('agent:executor', 'agent:invoke', 'execute'),
    ('agent:executor', 'agent:info', 'read')
ON CONFLICT DO NOTHING;

-- Default permissions for orchestrator role
INSERT INTO permissions (role_name, resource, action) VALUES
    ('agent:orchestrator', 'memory:read', 'read'),
    ('agent:orchestrator', 'memory:write', 'write'),
    ('agent:orchestrator', 'agent:invoke', 'execute'),
    ('agent:orchestrator', 'agent:invoke', 'orchestrate'),
    ('agent:orchestrator', 'agent:info', 'read'),
    ('agent:orchestrator', 'workflow:create', 'write')
ON CONFLICT DO NOTHING;

-- Default permissions for admin role
INSERT INTO permissions (role_name, resource, action) VALUES
    ('agent:admin', '*', '*')
ON CONFLICT DO NOTHING;
