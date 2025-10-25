#!/bin/bash
set -e

echo "🚀 Deploying Agent Economy OS to Kubernetes..."

# Configuration
NAMESPACE=${NAMESPACE:-agentos}
REGISTRY=${REGISTRY:-agentos}
VERSION=${VERSION:-0.1.0}

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl required"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm required"; exit 1; }

echo "✅ Prerequisites check passed"

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f infra/k8s/namespace.yaml

# Create secrets (if they don't exist)
echo "🔐 Creating secrets..."
kubectl apply -f infra/k8s/secrets.yaml

# Deploy infrastructure dependencies
echo "🗄️  Deploying infrastructure..."

# PostgreSQL
helm upgrade --install postgres bitnami/postgresql \
  --namespace $NAMESPACE \
  --set auth.database=agentos \
  --set auth.username=agentos \
  --set auth.password=${POSTGRES_PASSWORD:-changeme} \
  --set primary.persistence.size=50Gi \
  --wait

# Redis
helm upgrade --install redis bitnami/redis \
  --namespace $NAMESPACE \
  --set architecture=standalone \
  --set auth.password=${REDIS_PASSWORD:-changeme} \
  --set master.persistence.size=10Gi \
  --wait

# Qdrant
echo "📊 Deploying Qdrant..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.7.4
        ports:
        - containerPort: 6333
        - containerPort: 6334
        volumeMounts:
        - name: storage
          mountPath: /qdrant/storage
      volumes:
      - name: storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: $NAMESPACE
spec:
  selector:
    app: qdrant
  ports:
  - name: http
    port: 6333
  - name: grpc
    port: 6334
EOF

# Wait for infrastructure
echo "⏳ Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=qdrant -n $NAMESPACE --timeout=300s

# Run migrations
echo "🗄️  Running database migrations..."
kubectl run -i --rm --restart=Never migrate \
  --namespace=$NAMESPACE \
  --image=postgres:16-alpine \
  --env="PGPASSWORD=${POSTGRES_PASSWORD:-changeme}" \
  -- psql -h postgres -U agentos -d agentos < infra/migrations/001_initial_schema.sql || true

# Deploy application services
echo "🚀 Deploying application services..."

# Identity Service
helm upgrade --install identity ./infra/helm/identity \
  --namespace $NAMESPACE \
  --set image.repository=$REGISTRY/identity \
  --set image.tag=$VERSION \
  --wait

# Memory Service
helm upgrade --install memory ./infra/helm/memory \
  --namespace $NAMESPACE \
  --set image.repository=$REGISTRY/memory \
  --set image.tag=$VERSION \
  --wait

# Policy Engine
helm upgrade --install policy-engine ./infra/helm/policy-engine \
  --namespace $NAMESPACE \
  --set image.repository=$REGISTRY/policy-engine \
  --set image.tag=$VERSION \
  --wait

# Gateway
helm upgrade --install gateway ./infra/helm/gateway \
  --namespace $NAMESPACE \
  --set image.repository=$REGISTRY/gateway \
  --set image.tag=$VERSION \
  --wait

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n $NAMESPACE

echo ""
echo "✨ Deployment complete!"
echo ""
echo "To access the services:"
echo "  kubectl port-forward -n $NAMESPACE svc/gateway 8080:8080"
echo ""
echo "To view logs:"
echo "  kubectl logs -n $NAMESPACE -l app=gateway --tail=50"
echo ""
echo "To get service endpoints:"
echo "  kubectl get svc -n $NAMESPACE"
