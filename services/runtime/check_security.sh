#!/bin/bash

# AgentOS Security Audit Script
# Checks RBAC, access logs, and security violations

set -e

echo "======================================================================================================="
echo "AGENTOS SECURITY AUDIT - $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================================================="

# Database connection parameters
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-agentos}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASS="${POSTGRES_PASSWORD:-postgres}"

# Function to run SQL queries
run_query() {
    local query="$1"
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$query" 2>/dev/null || echo "Query failed or table doesn't exist"
}

echo ""
echo "🔐 1. RBAC ROLES & PERMISSIONS"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    r.name as role,
    r.description,
    COUNT(p.id) as permissions_count
FROM roles r
LEFT JOIN permissions p ON r.name = p.role_name
GROUP BY r.name, r.description
ORDER BY r.name;
"

echo ""
echo "🔑 2. AGENT ROLE ASSIGNMENTS"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    ar.agent_did,
    ar.role_name,
    ar.granted_at,
    ar.granted_by,
    CASE 
        WHEN ar.expires_at IS NULL THEN 'Never'
        WHEN ar.expires_at > NOW() THEN 'Active'
        ELSE 'Expired'
    END as expiration_status
FROM agent_roles ar
ORDER BY ar.granted_at DESC
LIMIT 20;
"

echo ""
echo "📋 3. RECENT ACCESS ATTEMPTS (Last 24 Hours)"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    timestamp,
    agent_did,
    action,
    resource,
    status,
    metadata->>'ip_address' as ip_address
FROM agent_audit_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 20;
"

echo ""
echo "🚫 4. DENIED ACCESS ATTEMPTS (Security Violations)"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    timestamp,
    agent_did,
    action,
    resource,
    metadata->>'reason' as denial_reason
FROM agent_audit_logs
WHERE status = 'denied' AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 20;
"

echo ""
echo "⚠️  5. CONTENT POLICY VIOLATIONS"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    cv.created_at,
    cv.agent_did,
    cv.violation_type,
    cv.severity,
    cv.details->>'description' as description
FROM content_violations cv
WHERE cv.created_at > NOW() - INTERVAL '7 days'
ORDER BY cv.created_at DESC
LIMIT 20;
"

echo ""
echo "📊 6. SECURITY SUMMARY (Last 24 Hours)"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    action,
    status,
    COUNT(*) as count
FROM agent_audit_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY action, status
ORDER BY count DESC;
"

echo ""
echo "🔍 7. PERMISSION CHECKS (Sample Agents)"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    ar.agent_did,
    ar.role_name,
    p.resource,
    p.action,
    p.constraints
FROM agent_roles ar
JOIN permissions p ON ar.role_name = p.role_name
WHERE ar.agent_did IN (
    SELECT agent_did FROM agent_deployments ORDER BY deployed_at DESC LIMIT 5
)
ORDER BY ar.agent_did, p.resource;
"

echo ""
echo "💡 8. AGENTS WITHOUT ROLES (Potential Security Risk)"
echo "-------------------------------------------------------------------------------------------------------"
run_query "
SELECT 
    d.agent_did,
    d.status,
    d.deployed_at
FROM agent_deployments d
LEFT JOIN agent_roles ar ON d.agent_did = ar.agent_did
WHERE ar.agent_did IS NULL AND d.status = 'RUNNING'
ORDER BY d.deployed_at DESC;
"

echo ""
echo "======================================================================================================="
echo "✅ SECURITY AUDIT COMPLETE"
echo "======================================================================================================="
echo ""
echo "Next Steps:"
echo "  • Review denied access attempts for suspicious activity"
echo "  • Ensure all active agents have appropriate roles assigned"
echo "  • Monitor content violations for policy breaches"
echo "  • Update RBAC policies as needed: UPDATE permissions SET ... WHERE role_name = '...';"
echo ""
