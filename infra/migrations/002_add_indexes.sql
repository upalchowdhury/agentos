-- Additional indexes for performance optimization

-- Composite index for credential verification
CREATE INDEX IF NOT EXISTS idx_credentials_subject_expires 
    ON credentials(subject_did, expires_at) 
    WHERE revoked_at IS NULL;

-- Index for active (non-revoked) credentials
CREATE INDEX IF NOT EXISTS idx_credentials_active 
    ON credentials(subject_did) 
    WHERE revoked_at IS NULL;

-- Partial index for recent interactions (last 30 days)
CREATE INDEX IF NOT EXISTS idx_interactions_recent 
    ON interactions(created_at, conversation_id) 
    WHERE created_at > NOW() - INTERVAL '30 days';

-- Index for memory content search (for full-text search if needed)
CREATE INDEX IF NOT EXISTS idx_memories_content_gin 
    ON memories USING gin(to_tsvector('english', content));

-- Index for cost events aggregation
CREATE INDEX IF NOT EXISTS idx_cost_events_agent_time 
    ON cost_events(agent_did, created_at DESC, cost_cents);
