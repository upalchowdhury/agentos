#!/bin/bash
set -e

echo "🚀 Agent Economy OS - Quick Deployment Script"
echo "=============================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

# Check Docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Check kubectl context
CONTEXT=$(kubectl config current-context)
echo "✅ kubectl context: $CONTEXT"

if [ "$CONTEXT" != "docker-desktop" ]; then
    echo "⚠️  Context is not docker-desktop. Continue? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 0
    fi
fi

echo ""
echo "📦 Step 1/5: Building Docker images..."
echo "========================================"

# Build Gateway
echo "Building Gateway..."
docker build -t agentos/gateway:0.1.0 -f services/gateway/Dockerfile services/gateway
echo "✅ Gateway built"

# Build Identity  
echo "Building Identity..."
docker build -t agentos/identity:0.1.0 -f services/identity/Dockerfile services/identity
echo "✅ Identity built"

# Build Memory
echo "Building Memory..."
docker build -t agentos/memory:0.1.0 -f services/memory/Dockerfile services/memory
echo "✅ Memory built"

# Build Policy Engine
echo "Building Policy Engine..."
docker build -t agentos/policy-engine:0.1.0 -f services/policy-engine/Dockerfile services/policy-engine
echo "✅ Policy Engine built"

# Build Web UI
echo "Building Web UI..."
docker build -t agentos/web-ui:0.1.0 -f services/web-ui/Dockerfile services/web-ui
echo "✅ Web UI built"

echo ""
echo "☸️  Step 2/5: Creating namespace and configs..."
echo "================================================"

kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/postgres-init-configmap.yaml

echo "✅ Namespace and configs created"

echo ""
echo "💾 Step 3/5: Deploying databases..."
echo "===================================="

kubectl apply -f k8s/03-postgres.yaml
kubectl apply -f k8s/04-redis.yaml
kubectl apply -f k8s/05-qdrant.yaml
kubectl apply -f k8s/06-clickhouse.yaml

echo "⏳ Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n agentos --timeout=300s || echo "⚠️  Postgres timeout, continuing..."
kubectl wait --for=condition=ready pod -l app=redis -n agentos --timeout=300s || echo "⚠️  Redis timeout, continuing..."
kubectl wait --for=condition=ready pod -l app=qdrant -n agentos --timeout=300s || echo "⚠️  Qdrant timeout, continuing..."

echo "✅ Databases deployed"

echo ""
echo "🔧 Step 4/5: Deploying application services..."
echo "==============================================="

kubectl apply -f k8s/07-identity.yaml
kubectl apply -f k8s/08-memory.yaml
kubectl apply -f k8s/09-policy-engine.yaml
kubectl apply -f k8s/10-gateway.yaml
kubectl apply -f k8s/11-web-ui.yaml
kubectl apply -f k8s/12-ingress.yaml

echo "✅ Services deployed"

echo ""
echo "⏳ Step 5/5: Waiting for services to be ready..."
echo "================================================="

echo "Waiting for Identity service..."
kubectl wait --for=condition=ready pod -l app=identity -n agentos --timeout=180s || echo "⚠️  Identity timeout"

echo "Waiting for Gateway service..."
kubectl wait --for=condition=ready pod -l app=gateway -n agentos --timeout=180s || echo "⚠️  Gateway timeout"

echo "Waiting for Web UI..."
kubectl wait --for=condition=ready pod -l app=web-ui -n agentos --timeout=180s || echo "⚠️  Web UI timeout"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Checking pod status..."
kubectl get pods -n agentos

echo ""
echo "🌐 Access the application:"
echo "=========================="
echo ""
echo "Option 1: Port Forward (Recommended)"
echo "  kubectl port-forward -n agentos svc/web-ui 3001:80"
echo "  kubectl port-forward -n agentos svc/gateway 8080:8080"
echo "  Then open: http://localhost:3001"
echo ""
echo "Option 2: Ingress (requires setup)"
echo "  Add to /etc/hosts: 127.0.0.1 agentos.local"
echo "  Then open: http://agentos.local"
echo ""
echo "📝 Useful commands:"
echo "  kubectl get all -n agentos              # View all resources"
echo "  kubectl logs -n agentos -l app=gateway  # View Gateway logs"
echo "  kubectl describe pod -n agentos <pod>   # Debug pod issues"
echo ""
echo "🎉 Happy agent building!"
