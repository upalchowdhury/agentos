package router

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/agent-economy-os/gateway/pkg/types"
)

func TestRouteRequest_ValidationErrors(t *testing.T) {
	tests := []struct {
		name    string
		req     *types.AgentRequest
		wantErr bool
		errMsg  string
	}{
		{
			name: "missing caller_did",
			req: &types.AgentRequest{
				TargetDID: "did:agent:target",
				Action:    "execute",
			},
			wantErr: true,
			errMsg:  "caller_did required",
		},
		{
			name: "missing target_did",
			req: &types.AgentRequest{
				CallerDID: "did:agent:caller",
				Action:    "execute",
			},
			wantErr: true,
			errMsg:  "target_did required",
		},
		{
			name: "missing action",
			req: &types.AgentRequest{
				CallerDID: "did:agent:caller",
				TargetDID: "did:agent:target",
			},
			wantErr: true,
			errMsg:  "action required",
		},
	}

	router := NewRouter(&Config{
		IdentityServiceURL: "http://localhost:3000",
		PolicyServiceURL:   "http://localhost:8081",
		MemoryServiceURL:   "http://localhost:8000",
	})

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := router.RouteRequest(context.Background(), tt.req)
			
			if (err != nil) != tt.wantErr {
				t.Errorf("RouteRequest() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			
			if err != nil && err.Error() != tt.errMsg {
				t.Errorf("RouteRequest() error message = %v, want %v", err.Error(), tt.errMsg)
			}
		})
	}
}

func TestRouteRequest_Success(t *testing.T) {
	// Mock identity service
	identityServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"valid": true,
			"did":   "did:agent:caller",
		})
	}))
	defer identityServer.Close()

	// Mock policy service
	policyServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"allowed": true,
		})
	}))
	defer policyServer.Close()

	// Mock memory service
	memoryServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"context": map[string]interface{}{},
		})
	}))
	defer memoryServer.Close()

	router := NewRouter(&Config{
		IdentityServiceURL: identityServer.URL,
		PolicyServiceURL:   policyServer.URL,
		MemoryServiceURL:   memoryServer.URL,
	})

	req := &types.AgentRequest{
		CallerDID:      "did:agent:caller",
		TargetDID:      "did:agent:target",
		ConversationID: "conv-123",
		Action:         "execute",
		Credential:     "test-credential",
		Params:         map[string]interface{}{"task": "test"},
	}

	resp, err := router.RouteRequest(context.Background(), req)
	if err != nil {
		t.Fatalf("RouteRequest() unexpected error: %v", err)
	}

	if resp == nil {
		t.Fatal("RouteRequest() returned nil response")
	}

	if !resp.Success {
		t.Error("RouteRequest() expected success=true")
	}
}

func TestRouteRequest_PolicyDenied(t *testing.T) {
	// Mock identity service (allow)
	identityServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"valid": true,
		})
	}))
	defer identityServer.Close()

	// Mock policy service (deny)
	policyServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"allowed": false,
			"reason":  "rate limit exceeded",
		})
	}))
	defer policyServer.Close()

	router := NewRouter(&Config{
		IdentityServiceURL: identityServer.URL,
		PolicyServiceURL:   policyServer.URL,
		MemoryServiceURL:   "http://localhost:8000",
	})

	req := &types.AgentRequest{
		CallerDID:  "did:agent:caller",
		TargetDID:  "did:agent:target",
		Action:     "execute",
		Credential: "test-credential",
	}

	_, err := router.RouteRequest(context.Background(), req)
	if err == nil {
		t.Fatal("RouteRequest() expected error for policy denial")
	}

	if err.Error() != "policy denied" {
		t.Errorf("RouteRequest() error = %v, want 'policy denied'", err.Error())
	}
}
