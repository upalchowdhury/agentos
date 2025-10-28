package agentos.authz

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow if user owns the agent
allow if {
    input.subject_type == "user"
    input.agent.owner_id == input.subject.id
}

# Allow if user has role that permits invocation
allow if {
    input.subject_type == "user"
    role := data.roles[input.subject.roles[_]]
    role.permissions[_].resource == "agent:invoke"
    role.permissions[_].action == "execute"
}

# Allow A2A (agent-to-agent) invocation if explicitly permitted
allow if {
    input.subject_type == "agent"
    input.caller_agent_id
    a2a_permission_exists(input.caller_agent_id, input.agent_id)
}

# Check if A2A permission exists in database or policy
a2a_permission_exists(caller_id, target_id) if {
    perm := data.a2a_permissions[_]
    perm.caller_agent_id == caller_id
    perm.target_agent_id == target_id
    perm.action == "invoke"
    not perm.revoked
}

# Allow admin users for any operation
allow if {
    input.subject.roles[_] == "admin"
}

# Obligations: actions that must be taken if request is allowed
obligations := o {
    allow
    o := {
        "content_filter": content_filter_required,
        "pii_redaction": pii_redaction_required,
        "rate_limit": rate_limit_config,
        "audit_log": true
    }
}

# Content filtering required if agent handles sensitive data
content_filter_required if {
    input.agent.metadata.sensitive_data == true
}

# PII redaction required based on user consent
pii_redaction_required if {
    input.subject.privacy_settings.pii_redaction == true
}

# Rate limit based on user tier
rate_limit_config := limit if {
    input.subject.tier == "free"
    limit := {"rps": 1, "burst": 5}
} else := limit if {
    input.subject.tier == "pro"
    limit := {"rps": 10, "burst": 50}
} else := limit if {
    input.subject.tier == "enterprise"
    limit := {"rps": 100, "burst": 200}
}

# Deny reasons (for audit trail)
deny_reason := reason if {
    not allow
    input.subject_type == "user"
    input.agent.owner_id != input.subject.id
    reason := "user_not_owner"
} else := reason if {
    not allow
    input.subject_type == "agent"
    not a2a_permission_exists(input.caller_agent_id, input.agent_id)
    reason := "a2a_permission_denied"
} else := reason if {
    not allow
    reason := "unauthorized"
}
