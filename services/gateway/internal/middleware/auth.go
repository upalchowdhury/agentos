package middleware

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type contextKey string

const CallerDIDKey contextKey = "caller_did"

// Authentication middleware verifies JWT tokens with the identity service
func Authentication(identityServiceURL string) func(http.Handler) http.Handler {
	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/health" || r.URL.Path == "/metrics" {
				next.ServeHTTP(w, r)
				return
			}

			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				http.Error(w, `{"error":"missing authorization header"}`, http.StatusUnauthorized)
				return
			}

			token := strings.TrimPrefix(authHeader, "Bearer ")
			if token == authHeader {
				http.Error(w, `{"error":"invalid authorization format"}`, http.StatusUnauthorized)
				return
			}

			did, err := verifyToken(r.Context(), client, identityServiceURL, token)
			if err != nil {
				http.Error(w, fmt.Sprintf(`{"error":"token verification failed: %s"}`, err.Error()), http.StatusUnauthorized)
				return
			}

			ctx := context.WithValue(r.Context(), CallerDIDKey, did)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func verifyToken(ctx context.Context, client *http.Client, serviceURL, token string) (string, error) {
	reqBody := map[string]string{"credential": token}
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", serviceURL+"/api/v1/credentials/verify", strings.NewReader(string(jsonData)))
	if err != nil {
		return "", fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("verification failed with status %d", resp.StatusCode)
	}

	var result struct {
		Valid bool   `json:"valid"`
		DID   string `json:"did"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("decode response: %w", err)
	}

	if !result.Valid {
		return "", fmt.Errorf("token invalid")
	}

	return result.DID, nil
}

// GetCallerDID extracts the caller DID from the request context
func GetCallerDID(ctx context.Context) string {
	did, ok := ctx.Value(CallerDIDKey).(string)
	if !ok {
		return ""
	}
	return did
}
