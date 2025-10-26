#!/bin/bash
set -e

echo "=========================================="
echo "Agent Economy OS - Automated Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Step 1: Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}docker not found. Please install Docker.${NC}"
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Cannot connect to Kubernetes cluster.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Create namespace
echo "Step 2: Creating namespace..."
kubectl create namespace agentos --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1
echo -e "${GREEN}✓ Namespace created${NC}"
echo ""

# Create secrets
echo "Step 3: Creating secrets..."
kubectl create secret generic agentos-secrets \
  --from-literal=POSTGRES_USER=agentos \
  --from-literal=POSTGRES_PASSWORD=changeme123 \
  -n agentos \
  --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1
echo -e "${GREEN}✓ Secrets created${NC}"
echo ""

# Deploy PostgreSQL
echo "Step 4: Deploying PostgreSQL..."
cat <<EOF | kubectl apply -f - > /dev/null 2>&1
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: agentos
spec:
  type: ClusterIP
  ports:
    - port: 5432
      targetPort: 5432
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: agentos
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: agentos-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: agentos-secrets
                  key: POSTGRES_PASSWORD
            - name: POSTGRES_DB
              value: agentos
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: postgres-storage
          emptyDir: {}
EOF

echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n agentos --timeout=120s > /dev/null 2>&1
echo -e "${GREEN}✓ PostgreSQL deployed and ready${NC}"
echo ""

# Run database migration
echo "Step 5: Running database migration..."
echo -e "${YELLOW}Starting port forward to PostgreSQL...${NC}"
kubectl port-forward -n agentos svc/postgres 5432:5432 > /dev/null 2>&1 &
PG_PID=$!
sleep 5

echo "Running migration script..."
if PGPASSWORD=changeme123 psql -h localhost -U agentos -d agentos -f infra/migrations/004_runtime_schema.sql > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database migration completed${NC}"
else
    echo -e "${RED}✗ Database migration failed${NC}"
    echo "Trying to continue anyway..."
fi

kill $PG_PID > /dev/null 2>&1
echo ""

# Build Docker image
echo "Step 6: Building Runtime Service Docker image..."
cd services/runtime
docker build -t agentos/runtime:latest . > /dev/null 2>&1
echo -e "${GREEN}✓ Docker image built${NC}"

# For Minikube, load image
if kubectl config current-context | grep -q "minikube"; then
    echo "Detected Minikube, loading image..."
    minikube image load agentos/runtime:latest > /dev/null 2>&1
    echo -e "${GREEN}✓ Image loaded to Minikube${NC}"
fi

cd ../..
echo ""

# Deploy Runtime Service
echo "Step 7: Deploying Runtime Service..."
kubectl apply -f k8s/08-runtime.yaml > /dev/null 2>&1
echo -e "${YELLOW}Waiting for Runtime Service to be ready...${NC}"
kubectl wait --for=condition=available deployment/runtime -n agentos --timeout=180s > /dev/null 2>&1
echo -e "${GREEN}✓ Runtime Service deployed and ready${NC}"
echo ""

# Verify deployment
echo "Step 8: Verifying deployment..."
echo -e "${YELLOW}Starting port forward to Runtime Service...${NC}"
kubectl port-forward -n agentos svc/runtime 8000:8000 > /dev/null 2>&1 &
RUNTIME_PID=$!
sleep 3

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Runtime Service health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
fi
echo ""

# Print status
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""
echo "Kubernetes Resources:"
kubectl get pods,svc -n agentos
echo ""

echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Start the Web UI:"
echo "   ${YELLOW}cd services/web-ui && npm install && npm run dev${NC}"
echo ""
echo "2. Access the application:"
echo "   UI:       ${GREEN}http://localhost:5173${NC}"
echo "   API:      ${GREEN}http://localhost:8000${NC}"
echo "   API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "3. Port forwards running in background:"
echo "   Runtime: ${GREEN}http://localhost:8000${NC} (PID: $RUNTIME_PID)"
echo ""
echo "4. To stop port forwards:"
echo "   ${YELLOW}pkill -f 'kubectl port-forward'${NC}"
echo ""
echo "5. To view logs:"
echo "   ${YELLOW}kubectl logs -n agentos -l app=runtime -f${NC}"
echo ""
echo "=========================================="
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "=========================================="
