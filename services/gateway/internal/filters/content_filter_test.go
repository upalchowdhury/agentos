package filters

import (
	"context"
	"testing"
)

func TestPIIDetector(t *testing.T) {
	detector := NewPIIDetector()

	tests := []struct {
		name     string
		input    map[string]interface{}
		expected int
	}{
		{
			name: "detect SSN",
			input: map[string]interface{}{
				"message": "My SSN is 123-45-6789",
			},
			expected: 1,
		},
		{
			name: "detect email",
			input: map[string]interface{}{
				"contact": "user@example.com",
			},
			expected: 1,
		},
		{
			name: "detect credit card",
			input: map[string]interface{}{
				"payment": "Card: 4532-1234-5678-9010",
			},
			expected: 1,
		},
		{
			name: "no PII",
			input: map[string]interface{}{
				"message": "Hello world",
			},
			expected: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			matches := detector.Detect(tt.input)
			if len(matches) != tt.expected {
				t.Errorf("expected %d matches, got %d", tt.expected, len(matches))
			}
		})
	}
}

func TestToxicityChecker(t *testing.T) {
	checker := NewToxicityChecker()

	tests := []struct {
		name          string
		input         map[string]interface{}
		expectToxic   bool
		minScore      float64
	}{
		{
			name: "clean content",
			input: map[string]interface{}{
				"message": "Hello, how are you?",
			},
			expectToxic: false,
			minScore:    0.0,
		},
		{
			name: "toxic content",
			input: map[string]interface{}{
				"message": "I will kill you",
			},
			expectToxic: true,
			minScore:    0.1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			score, types := checker.Score(tt.input)
			
			if tt.expectToxic && score < tt.minScore {
				t.Errorf("expected toxic content with score >= %f, got %f", tt.minScore, score)
			}
			
			if !tt.expectToxic && score > 0 {
				t.Errorf("expected clean content, got toxic score %f with types %v", score, types)
			}
		})
	}
}

func TestContentFilter_ScanRequest(t *testing.T) {
	filter := NewContentFilter()
	ctx := context.Background()

	tests := []struct {
		name        string
		request     *AgentRequest
		expectError bool
	}{
		{
			name: "clean request",
			request: &AgentRequest{
				CallerDID: "did:agent:test",
				Params: map[string]interface{}{
					"task": "analyze data",
				},
			},
			expectError: false,
		},
		{
			name: "request with PII",
			request: &AgentRequest{
				CallerDID: "did:agent:test",
				Params: map[string]interface{}{
					"task": "process SSN 123-45-6789",
				},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := filter.ScanRequest(ctx, tt.request)
			
			if tt.expectError && err == nil {
				t.Error("expected error, got nil")
			}
			
			if !tt.expectError && err != nil {
				t.Errorf("expected no error, got %v", err)
			}
		})
	}
}
