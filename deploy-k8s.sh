#!/bin/bash
# Deploy AgentOS Observability Stack to Kubernetes (Docker Desktop)

set -e

echo "🚀 Deploying AgentOS Observability Stack to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Is Docker Desktop Kubernetes enabled?"
    exit 1
fi

echo "✅ Kubernetes cluster accessible"

# Step 1: Deploy namespace and services
echo ""
echo "📦 Step 1: Deploying namespace and core services..."
kubectl apply -f infra/k8s/observability-stack.yaml

echo ""
echo "⏳ Waiting for PostgreSQL to be ready (this may take 30-60 seconds)..."
kubectl wait --for=condition=ready pod -l app=postgres -n agentos --timeout=120s

# Step 2: Initialize database
echo ""
echo "🗄️  Step 2: Initializing database schema..."
kubectl apply -f infra/k8s/init-db-job.yaml

echo "⏳ Waiting for database initialization..."
kubectl wait --for=condition=complete job/init-db -n agentos --timeout=60s

echo ""
echo "✅ Database initialized successfully"

# Step 3: Wait for all services to be ready
echo ""
echo "⏳ Step 3: Waiting for all services to be ready..."

echo "  - Waiting for runtime service..."
kubectl wait --for=condition=ready pod -l app=runtime -n agentos --timeout=120s

echo "  - Waiting for ingest service..."
kubectl wait --for=condition=ready pod -l app=ingest -n agentos --timeout=120s

echo "  - Waiting for otel-bridge service..."
kubectl wait --for=condition=ready pod -l app=otel-bridge -n agentos --timeout=120s

echo "  - Waiting for observability-api service..."
kubectl wait --for=condition=ready pod -l app=observability-api -n agentos --timeout=120s

echo ""
echo "✅ All services are ready!"

# Step 4: Display service information
echo ""
echo "📊 Deployed Services:"
echo "===================="
kubectl get pods -n agentos
echo ""
kubectl get svc -n agentos

echo ""
echo "🌐 Service Endpoints (via NodePort):"
echo "======================================"
echo "Runtime API:         http://localhost:30000"
echo "ATP Ingest:          http://localhost:30001"
echo "Observability API:   http://localhost:30003"
echo ""
echo "API Documentation:"
echo "Runtime:             http://localhost:30000/docs"
echo "Ingest:              http://localhost:30001/docs"
echo "Observability:       http://localhost:30003/docs"

# Step 5: Health checks
echo ""
echo "🏥 Running health checks..."

sleep 5  # Give services a moment to fully start

check_health() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url/health" > /dev/null 2>&1; then
        echo "  ✅ $name: healthy"
        return 0
    else
        echo "  ⚠️  $name: not yet ready (may need more time)"
        return 1
    fi
}

check_health "Runtime" "http://localhost:30000"
check_health "Ingest" "http://localhost:30001"
check_health "Observability" "http://localhost:30003"

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Start the Model B test agent:"
echo "   cd testAgents && python model_b_agent.py"
echo ""
echo "2. Register the agent:"
echo "   ./test-model-b.sh register"
echo ""
echo "3. Invoke the agent:"
echo "   ./test-model-b.sh invoke <agent-id>"
echo ""
echo "To view logs:"
echo "  kubectl logs -f -l app=runtime -n agentos"
echo "  kubectl logs -f -l app=ingest -n agentos"
echo ""
echo "To delete deployment:"
echo "  kubectl delete namespace agentos"
