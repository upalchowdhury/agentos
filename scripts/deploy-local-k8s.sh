#!/bin/bash
set -e

echo "🚀 Deploying Agent Economy OS to Local Kubernetes..."

# Build images
echo "📦 Building Docker images..."
cd /Users/upalc/AgentOS/agentos
./scripts/build-images.sh

# Apply manifests in order
echo "🎯 Applying Kubernetes manifests..."
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/postgres-init-configmap.yaml

# Databases
kubectl apply -f k8s/03-postgres.yaml
kubectl apply -f k8s/04-redis.yaml
kubectl apply -f k8s/05-qdrant.yaml
kubectl apply -f k8s/06-clickhouse.yaml

# Wait for databases
echo "⏳ Waiting for databases..."
kubectl wait --for=condition=ready pod -l app=postgres -n agentos --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n agentos --timeout=300s
kubectl wait --for=condition=ready pod -l app=qdrant -n agentos --timeout=300s

# Services
kubectl apply -f k8s/07-identity.yaml
kubectl apply -f k8s/08-memory.yaml
kubectl apply -f k8s/09-policy-engine.yaml
kubectl apply -f k8s/10-gateway.yaml
kubectl apply -f k8s/11-web-ui.yaml
kubectl apply -f k8s/12-ingress.yaml

echo "✅ Deployment complete!"
echo ""
echo "Access the application:"
echo "  http://agentos.local (add to /etc/hosts)"
echo ""
echo "Or port-forward:"
echo "  kubectl port-forward -n agentos svc/web-ui 3001:80"
echo "  kubectl port-forward -n agentos svc/gateway 8080:8080"
