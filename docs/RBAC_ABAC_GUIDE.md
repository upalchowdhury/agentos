# RBAC/ABAC and Content Guardrails Guide

## Overview

The Agent Economy OS implements comprehensive Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC), and Content Guardrails to ensure secure and compliant agent interactions.

## Features

### 1. Role-Based Access Control (RBAC)

**Default Roles:**
- `agent:basic` - Read-only access to memory and agent info
- `agent:executor` - Can execute tasks and write to memory
- `agent:orchestrator` - Can invoke other agents and manage workflows
- `agent:admin` - Full administrative access

**Permissions:**
Each role has specific permissions defining what resources and actions are allowed.

### 2. Attribute-Based Access Control (ABAC)

Permissions can include constraints based on context attributes:
- Time-based access
- Environment restrictions
- Resource-specific rules
- Custom attribute matching

### 3. Content Guardrails

**PII Detection:**
- SSN (Social Security Numbers)
- Credit Card Numbers
- Email Addresses
- Phone Numbers
- IP Addresses

**Toxicity Detection:**
- Profanity filtering
- Hate speech detection
- Harassment identification
- Violence-related content

## API Usage

### Assign Role to Agent

```bash
curl -X POST http://localhost:3000/api/v1/rbac/roles/assign \
  -H "Content-Type: application/json" \
  -d '{
    "agentDID": "did:agent:abc-123",
    "roleName": "agent:executor",
    "grantedBy": "did:agent:admin-456"
  }'
```

### Check Permissions

```bash
curl -X POST http://localhost:3000/api/v1/rbac/check \
  -H "Content-Type: application/json" \
  -d '{
    "agentDID": "did:agent:abc-123",
    "resource": "agent:invoke",
    "action": "execute",
    "context": {
      "environment": "production",
      "time": "2025-10-25T12:00:00Z"
    }
  }'
```

### Get Agent Roles

```bash
curl http://localhost:3000/api/v1/rbac/roles/did:agent:abc-123
```

### List All Roles

```bash
curl http://localhost:3000/api/v1/rbac/roles
```

## Custom Role Creation

### Create Custom Role

```typescript
// Using the RBACManager
await rbacManager.createRole('custom:analyst', 'Data analyst role');

await rbacManager.addPermission(
  'custom:analyst',
  'data:read',
  'read',
  {
    dataset: { operator: 'in', value: ['public', 'shared'] },
    time_range: { operator: 'less_than', value: '90d' }
  }
);
```

### Permission Constraints

ABAC constraints support various operators:

```typescript
{
  "attribute_name": {
    "operator": "equals" | "not_equals" | "contains" | "greater_than" | "less_than" | "in",
    "value": <expected_value>
  }
}
```

**Example:**
```json
{
  "constraints": {
    "environment": {
      "operator": "in",
      "value": ["staging", "production"]
    },
    "cost_limit": {
      "operator": "less_than",
      "value": 1000
    }
  }
}
```

## Policy Engine Rules

### Enhanced Rules

The Policy Engine now supports additional rule types:

```rust
// Rust rule definitions
pub enum Rule {
    RateLimit { max_requests: u32, window_seconds: u64 },
    CostLimit { max_cost_cents: u64, window_seconds: u64 },
    RequireRole { roles: Vec<String> },
    RequirePermission { resource: String, action: String },
    AttributeMatch { attribute: String, operator: Operator, value: String },
    BlockPII { types: Vec<PIIType> },
    BlockToxicity { threshold: f32 },
    RequireContentCompliance { policies: Vec<String> },
}
```

### Example Policy Configuration

```json
{
  "rules": [
    {
      "type": "RequireRole",
      "roles": ["agent:executor", "agent:orchestrator"]
    },
    {
      "type": "BlockPII",
      "types": ["SSN", "CreditCard"]
    },
    {
      "type": "BlockToxicity",
      "threshold": 0.8
    },
    {
      "type": "RateLimit",
      "max_requests": 1000,
      "window_seconds": 60
    }
  ]
}
```

## Content Filtering

Content filtering is automatically applied at the Gateway level before requests are processed.

### PII Detection

```go
// Automatic detection patterns
patterns := map[string]*regexp.Regexp{
    "ssn":         regexp.MustCompile(`\b\d{3}-\d{2}-\d{4}\b`),
    "credit_card": regexp.MustCompile(`\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b`),
    "email":       regexp.MustCompile(`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`),
    "phone":       regexp.MustCompile(`\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`),
    "ip_address":  regexp.MustCompile(`\b(?:\d{1,3}\.){3}\d{1,3}\b`),
}
```

When PII is detected:
1. Request is blocked
2. Violation is logged to `content_violations` table
3. Error is returned to caller

### Toxicity Scoring

Toxicity is scored from 0.0 to 1.0:
- **0.0 - 0.3**: Clean content
- **0.3 - 0.6**: Moderate concern
- **0.6 - 0.8**: High concern
- **0.8 - 1.0**: Critical - Blocked

## Database Schema

### New Tables

```sql
-- Roles
CREATE TABLE roles (
    name VARCHAR(50) PRIMARY KEY,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Permissions
CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    role_name VARCHAR(50) REFERENCES roles(name),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    constraints JSONB
);

-- Agent Roles
CREATE TABLE agent_roles (
    agent_did VARCHAR(255) REFERENCES dids(id),
    role_name VARCHAR(50) REFERENCES roles(name),
    granted_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (agent_did, role_name)
);

-- Content Violations
CREATE TABLE content_violations (
    id UUID PRIMARY KEY,
    agent_did VARCHAR(255) NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    details JSONB,
    severity VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Monitoring & Auditing

### View Violations

```sql
-- Recent PII violations
SELECT agent_did, violation_type, severity, created_at 
FROM content_violations 
WHERE violation_type = 'pii_detected'
ORDER BY created_at DESC 
LIMIT 100;

-- Toxicity violations by agent
SELECT agent_did, COUNT(*) as violation_count
FROM content_violations
WHERE violation_type = 'toxic_content'
GROUP BY agent_did
ORDER BY violation_count DESC;
```

### Audit Role Changes

```sql
-- View role assignments
SELECT ar.agent_did, ar.role_name, ar.granted_at, ar.granted_by
FROM agent_roles ar
ORDER BY ar.granted_at DESC;
```

## Best Practices

1. **Principle of Least Privilege**: Assign minimal roles needed
2. **Regular Audits**: Review role assignments monthly
3. **Content Monitoring**: Set up alerts for violations
4. **Custom Rules**: Create role-specific constraints for sensitive operations
5. **Testing**: Test ABAC constraints in staging before production

## Integration Example

```typescript
// Check permission before sensitive operation
const hasPermission = await rbacManager.checkPermission(
  agentDID,
  'data:delete',
  'write',
  {
    environment: 'production',
    data_classification: 'sensitive'
  }
);

if (!hasPermission) {
  throw new Error('Insufficient permissions for this operation');
}

// Proceed with operation
await performSensitiveOperation();
```

## Troubleshooting

### Permission Denied Issues

1. Check agent roles: `GET /api/v1/rbac/roles/:agentDID`
2. Verify role permissions in database
3. Check ABAC constraints match context
4. Review audit logs

### Content Filter False Positives

1. Review patterns in `content_filter.go`
2. Adjust toxicity threshold if needed
3. Whitelist specific patterns (with caution)
4. Add exceptions for legitimate use cases

## Migration

To apply RBAC schema:

```bash
kubectl exec -it -n agentos deployment/postgres -- \
  psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/003_rbac_schema.sql
```

## Future Enhancements

- Machine learning-based toxicity detection
- Integration with external compliance APIs (e.g., Perspective API)
- Advanced PII redaction with format-preserving encryption
- Multi-tenancy support with tenant-level policies
- Audit log export to SIEM systems

---

**Version:** 0.1.0  
**Last Updated:** October 25, 2025
