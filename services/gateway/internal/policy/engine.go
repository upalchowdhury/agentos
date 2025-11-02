package policy

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"
)

// Engine manages and evaluates policy packs
type Engine struct {
	packs map[string]*PolicyPack
	mu    sync.RWMutex
	
	// Metrics
	evaluationCount  int64
	violationCount   int64
	totalLatencyMs   int64
}

// NewEngine creates a policy evaluation engine
func NewEngine() *Engine {
	engine := &Engine{
		packs: make(map[string]*PolicyPack),
	}
	
	// Register default packs
	engine.RegisterPack(NewA2APolicyPack())
	engine.RegisterPack(NewMCPPolicyPack())
	
	return engine
}

// RegisterPack adds a policy pack to the engine
func (e *Engine) RegisterPack(pack *PolicyPack) {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	e.packs[pack.ID] = pack
	log.Printf("Registered policy pack: %s (%s)", pack.Name, pack.ID)
}

// EvaluateRequest evaluates a request against all applicable policy packs
func (e *Engine) EvaluateRequest(ctx context.Context, req *Request) (*PolicyResult, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	start := time.Now()
	
	// Find applicable packs based on protocol
	applicablePacks := []*PolicyPack{}
	for _, pack := range e.packs {
		if pack.Protocol == "all" || pack.Protocol == req.Protocol {
			applicablePacks = append(applicablePacks, pack)
		}
	}
	
	if len(applicablePacks) == 0 {
		return &PolicyResult{Allowed: true, Violations: []PolicyViolation{}}, nil
	}
	
	// Evaluate all packs
	aggregateResult := &PolicyResult{
		Allowed:    true,
		Violations: []PolicyViolation{},
	}
	
	for _, pack := range applicablePacks {
		result := pack.Evaluate(req)
		
		if !result.Allowed {
			aggregateResult.Allowed = false
		}
		
		aggregateResult.Violations = append(aggregateResult.Violations, result.Violations...)
	}
	
	// Update metrics
	latency := time.Since(start)
	aggregateResult.Latency = latency
	
	e.evaluationCount++
	if !aggregateResult.Allowed {
		e.violationCount++
	}
	e.totalLatencyMs += latency.Milliseconds()
	
	// Log violations
	if len(aggregateResult.Violations) > 0 {
		log.Printf("Policy violations detected: %d violations, allowed=%v", 
			len(aggregateResult.Violations), aggregateResult.Allowed)
		
		for _, v := range aggregateResult.Violations {
			log.Printf("  - [%s] %s: %s", v.Severity, v.RuleID, v.Message)
		}
	}
	
	return aggregateResult, nil
}

// GetMetrics returns current engine metrics
func (e *Engine) GetMetrics() map[string]interface{} {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	avgLatencyMs := float64(0)
	if e.evaluationCount > 0 {
		avgLatencyMs = float64(e.totalLatencyMs) / float64(e.evaluationCount)
	}
	
	return map[string]interface{}{
		"total_evaluations": e.evaluationCount,
		"total_violations": e.violationCount,
		"avg_latency_ms": avgLatencyMs,
		"registered_packs": len(e.packs),
	}
}

// GetPackInfo returns information about registered packs
func (e *Engine) GetPackInfo() []map[string]interface{} {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	info := []map[string]interface{}{}
	
	for _, pack := range e.packs {
		enabledRules := 0
		for _, rule := range pack.Rules {
			if rule.Enabled {
				enabledRules++
			}
		}
		
		info = append(info, map[string]interface{}{
			"id":            pack.ID,
			"name":          pack.Name,
			"description":   pack.Description,
			"protocol":      pack.Protocol,
			"total_rules":   len(pack.Rules),
			"enabled_rules": enabledRules,
		})
	}
	
	return info
}

// UpdatePackRule enables or disables a specific rule
func (e *Engine) UpdatePackRule(packID, ruleID string, enabled bool) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	pack, ok := e.packs[packID]
	if !ok {
		return fmt.Errorf("policy pack not found: %s", packID)
	}
	
	for i := range pack.Rules {
		if pack.Rules[i].ID == ruleID {
			pack.Rules[i].Enabled = enabled
			log.Printf("Updated rule %s in pack %s: enabled=%v", ruleID, packID, enabled)
			return nil
		}
	}
	
	return fmt.Errorf("rule not found: %s in pack %s", ruleID, packID)
}

// ExportAuditLog exports policy evaluation results for compliance
func (e *Engine) ExportAuditLog(result *PolicyResult, req *Request) ([]byte, error) {
	audit := map[string]interface{}{
		"timestamp":    time.Now().Format(time.RFC3339),
		"protocol":     req.Protocol,
		"caller_did":   req.CallerDID,
		"target_did":   req.TargetDID,
		"allowed":      result.Allowed,
		"latency_ms":   result.Latency.Milliseconds(),
		"violations":   result.Violations,
	}
	
	return json.Marshal(audit)
}
