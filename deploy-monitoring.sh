#!/bin/bash
# Deploy Monitoring Stack (Grafana, Jaeger, Prometheus)

set -e

echo "🚀 Deploying AgentOS Monitoring Stack..."

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi

echo "✅ kubectl found"

# Deploy monitoring stack
echo ""
echo "📦 Deploying Jaeger, Grafana, and Prometheus..."
kubectl apply -f infra/k8s/monitoring-stack.yaml

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "  Waiting for Jaeger..."
kubectl wait --for=condition=ready pod -l app=jaeger -n agentos --timeout=120s || echo "  ⚠️  Jaeger taking longer..."

echo "  Waiting for Grafana..."
kubectl wait --for=condition=ready pod -l app=grafana -n agentos --timeout=120s || echo "  ⚠️  Grafana taking longer..."

echo "  Waiting for Prometheus..."
kubectl wait --for=condition=ready pod -l app=prometheus -n agentos --timeout=120s || echo "  ⚠️  Prometheus taking longer..."

echo ""
echo "✅ Monitoring Stack Deployed!"

echo ""
echo "🌐 Access URLs:"
echo "================================================"
echo "Jaeger UI (Tracing):    http://localhost:31686"
echo "Grafana (Dashboards):   http://localhost:31000"
echo "  Username: admin"
echo "  Password: admin"
echo "Prometheus (Metrics):   http://localhost:31090"
echo ""
echo "Observability API:      http://localhost:30003/docs"
echo "Runtime API:            http://localhost:30000/docs"
echo "================================================"

echo ""
echo "📊 Grafana Setup:"
echo "1. Open http://localhost:31000"
echo "2. Login with admin/admin"
echo "3. Go to Dashboards to create custom views"
echo "4. PostgreSQL datasource is pre-configured"

echo ""
echo "🔍 Jaeger Setup:"
echo "1. Open http://localhost:31686"
echo "2. Select 'agentos' service"
echo "3. Click 'Find Traces' to see all traces"

echo ""
kubectl get pods -n agentos | grep -E "(jaeger|grafana|prometheus)"

echo ""
echo "🎉 Monitoring stack ready for demo!"
