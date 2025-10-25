package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/agent-economy-os/gateway/internal/adapters/a2a"
	"github.com/agent-economy-os/gateway/internal/adapters/mcp"
	"github.com/agent-economy-os/gateway/internal/middleware"
	"github.com/agent-economy-os/gateway/internal/router"
	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func main() {
	ctx := context.Background()

	// Initialize tracing
	if err := initTracing(ctx); err != nil {
		log.Printf("Warning: failed to initialize tracing: %v", err)
	}

	// Initialize router with service URLs
	agentRouter := router.NewRouter(&router.Config{
		IdentityServiceURL: getEnv("IDENTITY_SERVICE_URL", "http://localhost:3000"),
		PolicyServiceURL:   getEnv("POLICY_SERVICE_URL", "http://localhost:8081"),
		MemoryServiceURL:   getEnv("MEMORY_SERVICE_URL", "http://localhost:8000"),
	})

	// Register protocol adapters
	a2aAdapter := a2a.NewAdapter(agentRouter)
	mcpAdapter := mcp.NewAdapter(agentRouter)

	// Setup router
	r := mux.NewRouter()

	// Middleware chain
	r.Use(middleware.RequestID)
	r.Use(middleware.LogRequest)
	r.Use(middleware.Authentication(getEnv("IDENTITY_SERVICE_URL", "http://localhost:3000")))
	r.Use(middleware.Tracing)
	r.Use(middleware.RateLimit)
	r.Use(middleware.Recovery)

	// Routes
	r.HandleFunc("/a2a/v1/invoke", a2aAdapter.HandleInvoke).Methods("POST")
	r.HandleFunc("/mcp/v1/call", mcpAdapter.HandleCall).Methods("POST")
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/metrics", promhttp.Handler().ServeHTTP).Methods("GET")

	// Server configuration
	srv := &http.Server{
		Addr:         ":8080",
		Handler:      r,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Start server
	go func() {
		log.Printf("Gateway listening on %s", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal(err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	log.Println("Server exited")
}

func initTracing(ctx context.Context) error {
	endpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if endpoint == "" {
		return nil // Tracing not configured
	}

	exporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithEndpoint(endpoint),
		otlptracegrpc.WithInsecure(),
	)
	if err != nil {
		return fmt.Errorf("create exporter: %w", err)
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName("gateway"),
			semconv.ServiceVersion("0.1.0"),
		),
	)
	if err != nil {
		return fmt.Errorf("create resource: %w", err)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)
	otel.SetTracerProvider(tp)

	return nil
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status":"healthy"}`)
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
