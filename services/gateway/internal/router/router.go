package router

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/agent-economy-os/gateway/pkg/types"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

type Router struct {
	config         *Config
	identityClient *http.Client
	policyClient   *http.Client
	memoryClient   *http.Client
	tracer         trace.Tracer
}

type Config struct {
	IdentityServiceURL string
	PolicyServiceURL   string
	MemoryServiceURL   string
}

func NewRouter(config *Config) *Router {
	return &Router{
		config: config,
		identityClient: &http.Client{
			Timeout: 5 * time.Second,
		},
		policyClient: &http.Client{
			Timeout: 5 * time.Second,
		},
		memoryClient: &http.Client{
			Timeout: 10 * time.Second,
		},
		tracer: otel.Tracer("gateway-router"),
	}
}

// RouteRequest handles intelligent routing with policy enforcement
func (r *Router) RouteRequest(ctx context.Context, req *types.AgentRequest) (*types.AgentResponse, error) {
	ctx, span := r.tracer.Start(ctx, "RouteRequest")
	defer span.End()

	span.SetAttributes(
		attribute.String("agent.caller", req.CallerDID),
		attribute.String("agent.target", req.TargetDID),
		attribute.String("agent.action", req.Action),
	)

	if req.CallerDID == "" {
		return nil, fmt.Errorf("caller_did required")
	}
	if req.TargetDID == "" {
		return nil, fmt.Errorf("target_did required")
	}
	if req.Action == "" {
		return nil, fmt.Errorf("action required")
	}

	// 1. Verify caller identity
	verified, err := r.verifyCredential(ctx, req.CallerDID, req.Credential)
	if err != nil {
		span.RecordError(err)
		return nil, fmt.Errorf("identity verification failed: %w", err)
	}
	if !verified {
		return nil, fmt.Errorf("identity verification failed")
	}

	// 2. Check policy
	allowed, err := r.evaluatePolicy(ctx, req)
	if err != nil {
		span.RecordError(err)
		return nil, fmt.Errorf("policy evaluation failed: %w", err)
	}
	if !allowed {
		return nil, fmt.Errorf("policy denied")
	}

	// 3. Load relevant memory/context
	memory, err := r.getContext(ctx, req.TargetDID, req.ConversationID)
	if err != nil {
		// Non-fatal, continue without memory
		span.RecordError(err)
	}

	// 4. Execute request (route to actual agent backend)
	resp, err := r.executeAgent(ctx, req, memory)
	if err != nil {
		span.RecordError(err)
		return nil, fmt.Errorf("agent execution failed: %w", err)
	}

	// 5. Store interaction in memory (async)
	go func() {
		bgCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		
		if err := r.storeInteraction(bgCtx, req, resp); err != nil {
			// Log error but don't fail the request
			fmt.Printf("failed to store interaction: %v\n", err)
		}
	}()

	return resp, nil
}

func (r *Router) verifyCredential(ctx context.Context, did, credential string) (bool, error) {
	reqBody := map[string]string{
		"credential": credential,
	}
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return false, fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", 
		r.config.IdentityServiceURL+"/api/v1/credentials/verify",
		bytes.NewReader(jsonData))
	if err != nil {
		return false, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := r.identityClient.Do(req)
	if err != nil {
		return false, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return false, nil
	}

	var result struct {
		Valid bool `json:"valid"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false, fmt.Errorf("decode response: %w", err)
	}

	return result.Valid, nil
}

func (r *Router) evaluatePolicy(ctx context.Context, req *types.AgentRequest) (bool, error) {
	policyReq := &types.PolicyRequest{
		CallerDID: req.CallerDID,
		TargetDID: req.TargetDID,
		Action:    req.Action,
		Context:   req.Context,
	}

	jsonData, err := json.Marshal(policyReq)
	if err != nil {
		return false, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST",
		r.config.PolicyServiceURL+"/api/v1/evaluate",
		bytes.NewReader(jsonData))
	if err != nil {
		return false, fmt.Errorf("create request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.policyClient.Do(httpReq)
	if err != nil {
		return false, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	var policyResp types.PolicyResponse
	if err := json.NewDecoder(resp.Body).Decode(&policyResp); err != nil {
		return false, fmt.Errorf("decode response: %w", err)
	}

	return policyResp.Allowed, nil
}

func (r *Router) getContext(ctx context.Context, targetDID, conversationID string) (*types.Memory, error) {
	url := fmt.Sprintf("%s/api/v1/context/%s?agent_did=%s&limit=50",
		r.config.MemoryServiceURL, conversationID, targetDID)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}

	resp, err := r.memoryClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("context fetch failed with status %d", resp.StatusCode)
	}

	var result struct {
		Context types.Memory `json:"context"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	return &result.Context, nil
}

func (r *Router) executeAgent(ctx context.Context, req *types.AgentRequest, memory *types.Memory) (*types.AgentResponse, error) {
	// In production, this would route to actual agent backends
	// For MVP, return success response
	return &types.AgentResponse{
		Success: true,
		Data: map[string]interface{}{
			"message": "agent executed successfully",
			"action":  req.Action,
		},
	}, nil
}

func (r *Router) storeInteraction(ctx context.Context, req *types.AgentRequest, resp *types.AgentResponse) error {
	interaction := map[string]interface{}{
		"caller_did":      req.CallerDID,
		"target_did":      req.TargetDID,
		"conversation_id": req.ConversationID,
		"request":         req,
		"response":        resp,
	}

	jsonData, err := json.Marshal(interaction)
	if err != nil {
		return fmt.Errorf("marshal interaction: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST",
		r.config.MemoryServiceURL+"/api/v1/interactions",
		bytes.NewReader(jsonData))
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	httpResp, err := r.memoryClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return fmt.Errorf("store interaction failed with status %d", httpResp.StatusCode)
	}

	return nil
}
