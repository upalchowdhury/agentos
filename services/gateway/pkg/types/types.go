package types

import "time"

// AgentRequest represents an incoming agent invocation request
type AgentRequest struct {
	CallerDID      string                 `json:"caller_did"`
	TargetDID      string                 `json:"target_did"`
	ConversationID string                 `json:"conversation_id"`
	Action         string                 `json:"action"`
	Params         map[string]interface{} `json:"params"`
	Credential     string                 `json:"credential"`
	Context        map[string]interface{} `json:"context"`
}

// AgentResponse represents the response from an agent invocation
type AgentResponse struct {
	Success bool                   `json:"success"`
	Data    map[string]interface{} `json:"data"`
	Error   string                 `json:"error,omitempty"`
}

// Memory represents contextual memory for an agent
type Memory struct {
	AgentDID       string                 `json:"agent_did"`
	ConversationID string                 `json:"conversation_id"`
	Content        string                 `json:"content"`
	Metadata       map[string]interface{} `json:"metadata"`
	Timestamp      time.Time              `json:"timestamp"`
}

// Interaction represents a logged agent interaction
type Interaction struct {
	CallerDID      string         `json:"caller_did"`
	TargetDID      string         `json:"target_did"`
	ConversationID string         `json:"conversation_id"`
	Request        *AgentRequest  `json:"request"`
	Response       *AgentResponse `json:"response"`
	Timestamp      time.Time      `json:"timestamp"`
}

// PolicyRequest represents a policy evaluation request
type PolicyRequest struct {
	CallerDID string                 `json:"caller_did"`
	TargetDID string                 `json:"target_did"`
	Action    string                 `json:"action"`
	Context   map[string]interface{} `json:"context"`
}

// PolicyResponse represents a policy evaluation response
type PolicyResponse struct {
	Allowed bool   `json:"allowed"`
	Reason  string `json:"reason,omitempty"`
}
