// Package middleware provides trace context propagation for W3C traceparent/tracestate
// and automatic edge creation for A2A/MCP flows.
package middleware

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/baggage"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/trace"
)

const (
	// Header names
	TraceParentHeader = "traceparent"
	TraceStateHeader  = "tracestate"
	BaggageHeader     = "baggage"

	// Baggage keys
	BaggageAgentID      = "agent_id"
	BaggageVersionID    = "version_id"
	BaggageTenantID     = "tenant_id"
	BaggageRunMode      = "run_mode"
	BaggageConfigHash   = "config_hash"
	BaggageBudget       = "budget_remaining_cents"

	// Edge tracking
	EdgeIDHeader = "x-agentos-edge-id"
	RequestIDHeader = "x-request-id"
)

// TraceContextMiddleware injects W3C trace context and creates inter-agent edges
type TraceContextMiddleware struct {
	tracer      trace.Tracer
	propagator  propagation.TextMapPropagator
	edgeTracker *EdgeTracker
}

// EdgeTracker records inter-agent communication edges
type EdgeTracker struct {
	RuntimeAPIURL string
	HTTPClient    *http.Client
}

// Edge represents an inter-agent communication event
type Edge struct {
	EdgeID           string    `json:"edge_id"`
	TraceID          string    `json:"trace_id"`
	FromAgentID      string    `json:"from_agent_id"`
	FromVersionID    string    `json:"from_version_id,omitempty"`
	FromSpanID       string    `json:"from_span_id"`
	ToAgentID        string    `json:"to_agent_id"`
	ToVersionID      string    `json:"to_version_id,omitempty"`
	ToSpanID         string    `json:"to_span_id"`
	Channel          string    `json:"channel"` // a2a, mcp, http, grpc
	InstructionType  string    `json:"instruction_type"` // prompt, tool_request, system_directive, callback
	Timestamp        time.Time `json:"timestamp"`
	LatencyMS        int       `json:"latency_ms,omitempty"`
	SizeBytes        int       `json:"size_bytes"`
	ContentHash      string    `json:"content_hash"`
	RedactionApplied bool      `json:"redaction_applied"`
	SignatureVerified bool     `json:"signature_verified"`
	PolicyEnforced   []string  `json:"policy_enforced,omitempty"`
	Obligations      []string  `json:"obligations,omitempty"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// NewTraceContextMiddleware creates a new trace context middleware
func NewTraceContextMiddleware(runtimeAPIURL string) *TraceContextMiddleware {
	return &TraceContextMiddleware{
		tracer:     otel.Tracer("agentos-gateway"),
		propagator: propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{}, // W3C traceparent/tracestate
			propagation.Baggage{},      // W3C baggage
		),
		edgeTracker: &EdgeTracker{
			RuntimeAPIURL: runtimeAPIURL,
			HTTPClient:    &http.Client{Timeout: 5 * time.Second},
		},
	}
}

// Handler wraps HTTP handlers with trace context propagation
func (m *TraceContextMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract existing trace context from incoming request
		ctx := m.propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))

		// Start a new span for this gateway hop
		spanName := fmt.Sprintf("%s %s", r.Method, r.URL.Path)
		ctx, span := m.tracer.Start(ctx, spanName,
			trace.WithSpanKind(trace.SpanKindServer),
			trace.WithAttributes(
				attribute.String("http.method", r.Method),
				attribute.String("http.url", r.URL.String()),
				attribute.String("http.scheme", r.URL.Scheme),
				attribute.String("http.target", r.URL.Path),
			),
		)
		defer span.End()

		// Extract baggage
		bag := baggage.FromContext(ctx)

		// Determine if this is an A2A or MCP call
		protocol := m.detectProtocol(r)
		isInterAgent := protocol == "a2a" || protocol == "mcp"

		// If inter-agent, create edge tracking
		var edgeID string
		var fromAgentID, toAgentID string

		if isInterAgent {
			edgeID = uuid.New().String()
			fromAgentID = bag.Member(BaggageAgentID).Value()
			toAgentID = m.extractTargetAgentID(r)

			// Inject edge ID into request headers
			r.Header.Set(EdgeIDHeader, edgeID)

			// Add span attributes
			span.SetAttributes(
				attribute.String("agentos.edge_id", edgeID),
				attribute.String("agentos.protocol", protocol),
				attribute.String("agentos.from_agent_id", fromAgentID),
				attribute.String("agentos.to_agent_id", toAgentID),
			)
		}

		// Read and hash request body for edge content tracking
		var bodyBytes []byte
		var contentHash string
		if r.Body != nil && isInterAgent {
			bodyBytes, _ = io.ReadAll(r.Body)
			r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))
			contentHash = hashContent(bodyBytes)
		}

		// Inject trace context into outgoing request (for proxying)
		m.propagator.Inject(ctx, propagation.HeaderCarrier(r.Header))

		// Ensure traceparent is present
		if r.Header.Get(TraceParentHeader) == "" {
			traceparent := m.createTraceparent(span.SpanContext())
			r.Header.Set(TraceParentHeader, traceparent)
		}

		// Wrap response writer to capture status code
		wrappedWriter := &statusRecorder{ResponseWriter: w, statusCode: http.StatusOK}

		// Record request start time
		startTime := time.Now()

		// Call next handler
		next.ServeHTTP(wrappedWriter, r.WithContext(ctx))

		// Calculate latency
		latencyMS := int(time.Since(startTime).Milliseconds())

		// Record span status based on HTTP status code
		if wrappedWriter.statusCode >= 400 {
			span.SetStatus(codes.Error, fmt.Sprintf("HTTP %d", wrappedWriter.statusCode))
		} else {
			span.SetStatus(codes.Ok, "")
		}

		span.SetAttributes(
			attribute.Int("http.status_code", wrappedWriter.statusCode),
			attribute.Int("http.response_size", wrappedWriter.bytesWritten),
		)

		// If inter-agent, record edge asynchronously
		if isInterAgent && fromAgentID != "" && toAgentID != "" {
			edge := Edge{
				EdgeID:           edgeID,
				TraceID:          span.SpanContext().TraceID().String(),
				FromAgentID:      fromAgentID,
				FromVersionID:    bag.Member(BaggageVersionID).Value(),
				FromSpanID:       bag.Member("parent_span_id").Value(), // From caller's span
				ToAgentID:        toAgentID,
				ToSpanID:         span.SpanContext().SpanID().String(),
				Channel:          protocol,
				InstructionType:  m.detectInstructionType(r),
				Timestamp:        startTime,
				LatencyMS:        latencyMS,
				SizeBytes:        len(bodyBytes),
				ContentHash:      contentHash,
				SignatureVerified: m.verifySignature(r),
				PolicyEnforced:   m.extractPolicyIDs(r),
				Obligations:      m.extractObligations(r),
				Metadata: map[string]interface{}{
					"http_method": r.Method,
					"http_path":   r.URL.Path,
					"http_status": wrappedWriter.statusCode,
				},
			}

			// Record edge asynchronously (non-blocking)
			go m.edgeTracker.RecordEdge(edge)
		}
	})
}

// detectProtocol determines the communication protocol
func (m *TraceContextMiddleware) detectProtocol(r *http.Request) string {
	if strings.HasPrefix(r.URL.Path, "/a2a/") {
		return "a2a"
	}
	if strings.HasPrefix(r.URL.Path, "/mcp/") {
		return "mcp"
	}
	if r.Header.Get("Content-Type") == "application/grpc" {
		return "grpc"
	}
	return "http"
}

// extractTargetAgentID extracts the target agent ID from request
func (m *TraceContextMiddleware) extractTargetAgentID(r *http.Request) string {
	// Try to extract from URL path
	// Format: /a2a/v1/invoke/{agent_id} or /mcp/v1/call/{agent_id}
	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) >= 5 {
		return pathParts[4] // agent_id position
	}

	// Try to extract from query params
	return r.URL.Query().Get("agent_id")
}

// detectInstructionType determines the instruction type
func (m *TraceContextMiddleware) detectInstructionType(r *http.Request) string {
	if strings.Contains(r.URL.Path, "invoke") {
		return "prompt"
	}
	if strings.Contains(r.URL.Path, "tool") || strings.Contains(r.URL.Path, "call") {
		return "tool_request"
	}
	if strings.Contains(r.URL.Path, "callback") {
		return "callback"
	}
	return "system_directive"
}

// verifySignature checks if request has valid signature
func (m *TraceContextMiddleware) verifySignature(r *http.Request) bool {
	// Placeholder: implement actual signature verification
	// Check for Authorization header with signature
	auth := r.Header.Get("Authorization")
	return auth != "" && strings.HasPrefix(auth, "Bearer ")
}

// extractPolicyIDs extracts enforced policy IDs from request context
func (m *TraceContextMiddleware) extractPolicyIDs(r *http.Request) []string {
	// Placeholder: extract from context or headers
	// Set by OPA middleware
	policyHeader := r.Header.Get("X-AgentOS-Policies")
	if policyHeader == "" {
		return nil
	}
	return strings.Split(policyHeader, ",")
}

// extractObligations extracts policy obligations from request context
func (m *TraceContextMiddleware) extractObligations(r *http.Request) []string {
	obligationHeader := r.Header.Get("X-AgentOS-Obligations")
	if obligationHeader == "" {
		return nil
	}
	return strings.Split(obligationHeader, ",")
}

// createTraceparent creates W3C traceparent header
func (m *TraceContextMiddleware) createTraceparent(sc trace.SpanContext) string {
	// Format: {version}-{trace_id}-{span_id}-{flags}
	version := "00"
	traceID := sc.TraceID().String()
	spanID := sc.SpanID().String()
	flags := "01" // Sampled

	return fmt.Sprintf("%s-%s-%s-%s", version, traceID, spanID, flags)
}

// RecordEdge sends edge data to runtime API
func (et *EdgeTracker) RecordEdge(edge Edge) {
	payload := map[string]interface{}{
		"edges": []Edge{edge},
	}

	data, err := json.Marshal(payload)
	if err != nil {
		fmt.Printf("Failed to marshal edge: %v\n", err)
		return
	}

	url := et.RuntimeAPIURL + "/v1/spans/edges/ingest"
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(data))
	if err != nil {
		fmt.Printf("Failed to create edge request: %v\n", err)
		return
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := et.HTTPClient.Do(req)
	if err != nil {
		fmt.Printf("Failed to record edge: %v\n", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("Edge recording failed: HTTP %d - %s\n", resp.StatusCode, string(body))
	}
}

// hashContent computes SHA256 hash of content
func hashContent(data []byte) string {
	hash := sha256.Sum256(data)
	return hex.EncodeToString(hash[:])
}

// statusRecorder wraps ResponseWriter to capture status code
type statusRecorder struct {
	http.ResponseWriter
	statusCode   int
	bytesWritten int
}

func (r *statusRecorder) WriteHeader(statusCode int) {
	r.statusCode = statusCode
	r.ResponseWriter.WriteHeader(statusCode)
}

func (r *statusRecorder) Write(data []byte) (int, error) {
	n, err := r.ResponseWriter.Write(data)
	r.bytesWritten += n
	return n, err
}
