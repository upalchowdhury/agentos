package filters

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
)

type ContentFilter struct {
	piiDetector     *PIIDetector
	toxicityChecker *ToxicityChecker
}

func NewContentFilter() *ContentFilter {
	return &ContentFilter{
		piiDetector:     NewPIIDetector(),
		toxicityChecker: NewToxicityChecker(),
	}
}

type AgentRequest struct {
	CallerDID string
	Params    map[string]interface{}
}

type PolicyViolation struct {
	Type     string
	Details  interface{}
	Severity string
}

func (v *PolicyViolation) Error() string {
	return fmt.Sprintf("%s violation: %v", v.Type, v.Details)
}

func (f *ContentFilter) ScanRequest(ctx context.Context, req *AgentRequest) error {
	if req == nil || req.Params == nil {
		return nil
	}

	piiMatches := f.piiDetector.Detect(req.Params)
	if len(piiMatches) > 0 {
		return &PolicyViolation{
			Type:     "pii_detected",
			Details:  piiMatches,
			Severity: "high",
		}
	}

	score, toxicTypes := f.toxicityChecker.Score(req.Params)
	if score > 0.8 {
		return &PolicyViolation{
			Type:     "toxic_content",
			Details:  map[string]interface{}{"score": score, "types": toxicTypes},
			Severity: "critical",
		}
	}

	return nil
}

type PIIMatch struct {
	Type     string
	Redacted string
	Location string
}

type PIIDetector struct {
	patterns map[string]*regexp.Regexp
}

func NewPIIDetector() *PIIDetector {
	return &PIIDetector{
		patterns: map[string]*regexp.Regexp{
			"ssn":         regexp.MustCompile(`\b\d{3}-\d{2}-\d{4}\b`),
			"credit_card": regexp.MustCompile(`\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b`),
			"email":       regexp.MustCompile(`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`),
			"phone":       regexp.MustCompile(`\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`),
			"ip_address":  regexp.MustCompile(`\b(?:\d{1,3}\.){3}\d{1,3}\b`),
		},
	}
}

func (d *PIIDetector) Detect(data interface{}) []PIIMatch {
	text := stringify(data)
	var matches []PIIMatch

	for piiType, pattern := range d.patterns {
		if pattern.MatchString(text) {
			matches = append(matches, PIIMatch{
				Type:     piiType,
				Redacted: pattern.ReplaceAllString(text, "[REDACTED]"),
				Location: "request_params",
			})
		}
	}
	return matches
}

type ToxicityChecker struct {
	patterns map[string]*regexp.Regexp
}

func NewToxicityChecker() *ToxicityChecker {
	return &ToxicityChecker{
		patterns: map[string]*regexp.Regexp{
			"profanity":    regexp.MustCompile(`(?i)\b(badword1|badword2|badword3)\b`),
			"hate_speech":  regexp.MustCompile(`(?i)\b(hateword1|hateword2)\b`),
			"harassment":   regexp.MustCompile(`(?i)\b(harass|threaten|intimidate)\b`),
			"violence":     regexp.MustCompile(`(?i)\b(kill|murder|attack|assault)\b`),
		},
	}
}

func (t *ToxicityChecker) Score(data interface{}) (float64, []string) {
	text := strings.ToLower(stringify(data))
	var detectedTypes []string
	matchCount := 0

	for toxicType, pattern := range t.patterns {
		if pattern.MatchString(text) {
			detectedTypes = append(detectedTypes, toxicType)
			matchCount++
		}
	}

	if matchCount == 0 {
		return 0.0, nil
	}

	score := float64(matchCount) / float64(len(t.patterns))
	if score > 1.0 {
		score = 1.0
	}

	return score, detectedTypes
}

func stringify(data interface{}) string {
	switch v := data.(type) {
	case string:
		return v
	case map[string]interface{}:
		var parts []string
		for _, value := range v {
			parts = append(parts, stringify(value))
		}
		return strings.Join(parts, " ")
	case []interface{}:
		var parts []string
		for _, item := range v {
			parts = append(parts, stringify(item))
		}
		return strings.Join(parts, " ")
	default:
		bytes, err := json.Marshal(v)
		if err != nil {
			return ""
		}
		return string(bytes)
	}
}

func HashContent(data interface{}) string {
	text := stringify(data)
	hash := sha256.Sum256([]byte(text))
	return hex.EncodeToString(hash[:])
}
