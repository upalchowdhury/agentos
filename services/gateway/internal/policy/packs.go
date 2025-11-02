package policy

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// PolicyPack represents a reusable policy bundle for A2A/MCP protocols
type PolicyPack struct {
	ID          string
	Name        string
	Description string
	Protocol    string // "a2a", "mcp", or "all"
	Rules       []PolicyRule
}

// PolicyRule is an individual check within a pack
type PolicyRule struct {
	ID       string
	Name     string
	Enabled  bool
	Severity string // "critical", "high", "medium", "low"
	Check    func(req *Request) *PolicyViolation
}

// Request represents an incoming request to validate
type Request struct {
	Protocol      string
	Headers       map[string]string
	Body          []byte
	CallerDID     string
	TargetDID     string
	Signature     string
	PublicKey     string
	Timestamp     time.Time
	PayloadSize   int
	AllowedDomains []string
	AllowedTools   []string
}

// PolicyViolation indicates a policy check failure
type PolicyViolation struct {
	RuleID   string
	Severity string
	Message  string
	Details  map[string]interface{}
}

// PolicyResult aggregates all policy checks
type PolicyResult struct {
	Allowed    bool
	Violations []PolicyViolation
	Latency    time.Duration
}

// A2A Policy Pack
func NewA2APolicyPack() *PolicyPack {
	return &PolicyPack{
		ID:          "a2a-standard-v1",
		Name:        "A2A Standard Policy Pack",
		Description: "Signature verification, schema validation, size limits for A2A protocol",
		Protocol:    "a2a",
		Rules: []PolicyRule{
			{
				ID:       "a2a-signature-verify",
				Name:     "A2A Signature Verification",
				Enabled:  true,
				Severity: "critical",
				Check:    checkA2ASignature,
			},
			{
				ID:       "a2a-timestamp-fresh",
				Name:     "A2A Timestamp Freshness",
				Enabled:  true,
				Severity: "high",
				Check:    checkTimestampFreshness,
			},
			{
				ID:       "a2a-payload-size",
				Name:     "A2A Payload Size Limit",
				Enabled:  true,
				Severity: "medium",
				Check:    checkPayloadSize,
			},
			{
				ID:       "a2a-schema-valid",
				Name:     "A2A Schema Validation",
				Enabled:  true,
				Severity: "high",
				Check:    checkA2ASchema,
			},
		},
	}
}

// MCP Policy Pack
func NewMCPPolicyPack() *PolicyPack {
	return &PolicyPack{
		ID:          "mcp-standard-v1",
		Name:        "MCP Standard Policy Pack",
		Description: "Tool allowlist, domain restrictions, PII scan for MCP protocol",
		Protocol:    "mcp",
		Rules: []PolicyRule{
			{
				ID:       "mcp-tool-allowlist",
				Name:     "MCP Tool Allowlist",
				Enabled:  true,
				Severity: "high",
				Check:    checkMCPToolAllowlist,
			},
			{
				ID:       "mcp-domain-allowlist",
				Name:     "MCP External Domain Allowlist",
				Enabled:  true,
				Severity: "high",
				Check:    checkDomainAllowlist,
			},
			{
				ID:       "mcp-payload-size",
				Name:     "MCP Payload Size Limit",
				Enabled:  true,
				Severity: "medium",
				Check:    checkPayloadSize,
			},
			{
				ID:       "mcp-pii-scan",
				Name:     "MCP PII Detection",
				Enabled:  true,
				Severity: "medium",
				Check:    checkPIIScan,
			},
		},
	}
}

// Evaluate runs all rules in a policy pack
func (p *PolicyPack) Evaluate(req *Request) *PolicyResult {
	start := time.Now()
	
	result := &PolicyResult{
		Allowed:    true,
		Violations: []PolicyViolation{},
	}
	
	for _, rule := range p.Rules {
		if !rule.Enabled {
			continue
		}
		
		if violation := rule.Check(req); violation != nil {
			result.Violations = append(result.Violations, *violation)
			
			// Critical violations block the request
			if violation.Severity == "critical" || violation.Severity == "high" {
				result.Allowed = false
			}
		}
	}
	
	result.Latency = time.Since(start)
	return result
}

// ===== RULE IMPLEMENTATIONS =====

func checkA2ASignature(req *Request) *PolicyViolation {
	if req.Signature == "" {
		return &PolicyViolation{
			RuleID:   "a2a-signature-verify",
			Severity: "critical",
			Message:  "Missing signature header",
		}
	}
	
	if req.PublicKey == "" {
		return &PolicyViolation{
			RuleID:   "a2a-signature-verify",
			Severity: "critical",
			Message:  "Missing public key for verification",
		}
	}
	
	// Decode signature and public key
	sigBytes, err := base64.StdEncoding.DecodeString(req.Signature)
	if err != nil {
		return &PolicyViolation{
			RuleID:   "a2a-signature-verify",
			Severity: "critical",
			Message:  "Invalid signature encoding",
			Details:  map[string]interface{}{"error": err.Error()},
		}
	}
	
	pubKeyBytes, err := base64.StdEncoding.DecodeString(req.PublicKey)
	if err != nil {
		return &PolicyViolation{
			RuleID:   "a2a-signature-verify",
			Severity: "critical",
			Message:  "Invalid public key encoding",
			Details:  map[string]interface{}{"error": err.Error()},
		}
	}
	
	// Verify Ed25519 signature
	pubKey := ed25519.PublicKey(pubKeyBytes)
	
	// Message to verify = canonical form of request
	message := canonicalRequestMessage(req)
	
	if !ed25519.Verify(pubKey, message, sigBytes) {
		return &PolicyViolation{
			RuleID:   "a2a-signature-verify",
			Severity: "critical",
			Message:  "Signature verification failed",
		}
	}
	
	return nil
}

func checkTimestampFreshness(req *Request) *PolicyViolation {
	if req.Timestamp.IsZero() {
		return &PolicyViolation{
			RuleID:   "a2a-timestamp-fresh",
			Severity: "high",
			Message:  "Missing timestamp",
		}
	}
	
	// Allow 5 minutes clock skew
	now := time.Now()
	maxAge := 5 * time.Minute
	
	if now.Sub(req.Timestamp) > maxAge {
		return &PolicyViolation{
			RuleID:   "a2a-timestamp-fresh",
			Severity: "high",
			Message:  "Request timestamp too old",
			Details: map[string]interface{}{
				"timestamp": req.Timestamp.Format(time.RFC3339),
				"age_seconds": now.Sub(req.Timestamp).Seconds(),
				"max_age_seconds": maxAge.Seconds(),
			},
		}
	}
	
	// Check for future timestamps (clock skew)
	if req.Timestamp.After(now.Add(maxAge)) {
		return &PolicyViolation{
			RuleID:   "a2a-timestamp-fresh",
			Severity: "high",
			Message:  "Request timestamp is in the future",
			Details: map[string]interface{}{
				"timestamp": req.Timestamp.Format(time.RFC3339),
			},
		}
	}
	
	return nil
}

func checkPayloadSize(req *Request) *PolicyViolation {
	const maxPayloadSize = 10 * 1024 * 1024 // 10MB
	
	if req.PayloadSize > maxPayloadSize {
		return &PolicyViolation{
			RuleID:   "payload-size",
			Severity: "medium",
			Message:  fmt.Sprintf("Payload exceeds size limit (%d MB)", maxPayloadSize/(1024*1024)),
			Details: map[string]interface{}{
				"size_bytes": req.PayloadSize,
				"limit_bytes": maxPayloadSize,
			},
		}
	}
	
	return nil
}

func checkA2ASchema(req *Request) *PolicyViolation {
	// Parse body as JSON
	var payload map[string]interface{}
	if err := json.Unmarshal(req.Body, &payload); err != nil {
		return &PolicyViolation{
			RuleID:   "a2a-schema-valid",
			Severity: "high",
			Message:  "Invalid JSON payload",
			Details:  map[string]interface{}{"error": err.Error()},
		}
	}
	
	// Check required A2A fields
	requiredFields := []string{"caller_did", "target_did", "action"}
	for _, field := range requiredFields {
		if _, ok := payload[field]; !ok {
			return &PolicyViolation{
				RuleID:   "a2a-schema-valid",
				Severity: "high",
				Message:  fmt.Sprintf("Missing required field: %s", field),
			}
		}
	}
	
	return nil
}

func checkMCPToolAllowlist(req *Request) *PolicyViolation {
	// Parse MCP request
	var payload map[string]interface{}
	if err := json.Unmarshal(req.Body, &payload); err != nil {
		return nil // Skip if not valid JSON
	}
	
	// Extract tool name
	toolName, ok := payload["tool"].(string)
	if !ok {
		return nil
	}
	
	// Check against allowlist
	if len(req.AllowedTools) == 0 {
		// No restrictions if allowlist is empty
		return nil
	}
	
	allowed := false
	for _, allowedTool := range req.AllowedTools {
		if toolName == allowedTool {
			allowed = true
			break
		}
	}
	
	if !allowed {
		return &PolicyViolation{
			RuleID:   "mcp-tool-allowlist",
			Severity: "high",
			Message:  fmt.Sprintf("Tool not in allowlist: %s", toolName),
			Details: map[string]interface{}{
				"tool": toolName,
				"allowed_tools": req.AllowedTools,
			},
		}
	}
	
	return nil
}

func checkDomainAllowlist(req *Request) *PolicyViolation {
	// Parse request to find external URLs
	var payload map[string]interface{}
	if err := json.Unmarshal(req.Body, &payload); err != nil {
		return nil
	}
	
	// Extract URLs from various fields
	urls := extractURLs(payload)
	
	// Check each URL against allowlist
	if len(req.AllowedDomains) == 0 {
		return nil // No restrictions
	}
	
	for _, url := range urls {
		domain := extractDomain(url)
		allowed := false
		
		for _, allowedDomain := range req.AllowedDomains {
			if strings.HasSuffix(domain, allowedDomain) {
				allowed = true
				break
			}
		}
		
		if !allowed {
			return &PolicyViolation{
				RuleID:   "mcp-domain-allowlist",
				Severity: "high",
				Message:  fmt.Sprintf("External domain not allowed: %s", domain),
				Details: map[string]interface{}{
					"url": url,
					"domain": domain,
					"allowed_domains": req.AllowedDomains,
				},
			}
		}
	}
	
	return nil
}

func checkPIIScan(req *Request) *PolicyViolation {
	// Simple PII detection (can be enhanced with ML models)
	body := string(req.Body)
	
	patterns := map[string]string{
		"ssn":         `\b\d{3}-\d{2}-\d{4}\b`,
		"credit_card": `\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b`,
		"email":       `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`,
	}
	
	detected := []string{}
	for piiType := range patterns {
		// In production, use proper regex matching
		if strings.Contains(strings.ToLower(body), piiType) {
			detected = append(detected, piiType)
		}
	}
	
	if len(detected) > 0 {
		return &PolicyViolation{
			RuleID:   "mcp-pii-scan",
			Severity: "medium",
			Message:  "Potential PII detected in payload",
			Details: map[string]interface{}{
				"pii_types": detected,
			},
		}
	}
	
	return nil
}

// Helper functions

func canonicalRequestMessage(req *Request) []byte {
	// Create canonical representation for signing
	canonical := fmt.Sprintf("%s|%s|%s|%d",
		req.CallerDID,
		req.TargetDID,
		req.Timestamp.Format(time.RFC3339),
		req.PayloadSize,
	)
	
	// Add body hash
	hash := sha256.Sum256(req.Body)
	canonical += "|" + base64.StdEncoding.EncodeToString(hash[:])
	
	return []byte(canonical)
}

func extractURLs(data interface{}) []string {
	urls := []string{}
	
	switch v := data.(type) {
	case string:
		if strings.HasPrefix(v, "http://") || strings.HasPrefix(v, "https://") {
			urls = append(urls, v)
		}
	case map[string]interface{}:
		for _, val := range v {
			urls = append(urls, extractURLs(val)...)
		}
	case []interface{}:
		for _, val := range v {
			urls = append(urls, extractURLs(val)...)
		}
	}
	
	return urls
}

func extractDomain(url string) string {
	// Simple domain extraction
	url = strings.TrimPrefix(url, "http://")
	url = strings.TrimPrefix(url, "https://")
	
	parts := strings.Split(url, "/")
	if len(parts) > 0 {
		return parts[0]
	}
	
	return url
}
