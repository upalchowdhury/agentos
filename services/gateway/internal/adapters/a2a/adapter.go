package a2a

import (
	"encoding/json"
	"net/http"

	"github.com/agent-economy-os/gateway/internal/router"
	"github.com/agent-economy-os/gateway/pkg/types"
)

// Adapter handles Agent-to-Agent (A2A) protocol requests
type Adapter struct {
	router *router.Router
}

func NewAdapter(r *router.Router) *Adapter {
	return &Adapter{router: r}
}

// HandleInvoke handles A2A invocation requests
func (a *Adapter) HandleInvoke(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req types.AgentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
		return
	}

	resp, err := a.router.RouteRequest(ctx, &req)
	if err != nil {
		http.Error(w, `{"error":"`+err.Error()+`"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
