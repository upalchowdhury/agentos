package agentos.a2a

default allow = false

# Allow if the caller has a valid agent token
allow {
    input.token.valid == true
    input.token.type == "agent"
}

# Allow intra-team calls
allow {
    input.source_agent.team == input.target_agent.team
}
