# Deploy Agent Economy OS - Quick Start Guide

## Prerequisites Check

Before deploying, ensure you have:
- ✓ Docker installed and running
- ✓ Kubernetes cluster (Docker Desktop K8s, Minikube, or cloud)
- ✓ kubectl configured
- ✓ PostgreSQL accessible (local or in cluster)
- ✓ Node.js 16+ installed

## Step 1: Verify Kubernetes

```bash
# Check cluster is running
kubectl cluster-info

# Check current context
kubectl config current-context

# Create namespace if it doesn't exist
kubectl create namespace agentos --dry-run=client -o yaml | kubectl apply -f -
```

## Step 2: Create Secrets

```bash
# Create PostgreSQL secrets
kubectl create secret generic agentos-secrets \
  --from-literal=POSTGRES_USER=agentos \
  --from-literal=POSTGRES_PASSWORD=changeme123 \
  -n agentos \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify secret created
kubectl get secrets -n agentos
```

## Step 3: Deploy PostgreSQL (if not already running)

```bash
# Create PostgreSQL deployment
cat <<EOF | kubectl apply -f -
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

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n agentos --timeout=120s
```

## Step 4: Run Database Migration

```bash
# Port forward to PostgreSQL
kubectl port-forward -n agentos svc/postgres 5432:5432 &
PG_PID=$!

# Wait a moment for port forward to establish
sleep 3

# Run migration
PGPASSWORD=changeme123 psql -h localhost -U agentos -d agentos -f infra/migrations/004_runtime_schema.sql

# Stop port forward
kill $PG_PID
```

## Step 5: Build Runtime Service Docker Image

```bash
# Build image
cd services/runtime
docker build -t agentos/runtime:latest .

# For Minikube, load image
# minikube image load agentos/runtime:latest

# For Docker Desktop K8s, image is already available
# For cloud K8s, push to registry:
# docker tag agentos/runtime:latest your-registry/agentos/runtime:latest
# docker push your-registry/agentos/runtime:latest

cd ../..
```

## Step 6: Deploy Runtime Service

```bash
# Deploy runtime service
kubectl apply -f k8s/08-runtime.yaml

# Wait for deployment to be ready
kubectl wait --for=condition=available deployment/runtime -n agentos --timeout=120s

# Check pod status
kubectl get pods -n agentos -l app=runtime

# Check logs
kubectl logs -n agentos -l app=runtime --tail=50
```

## Step 7: Verify Runtime Service

```bash
# Port forward to runtime service
kubectl port-forward -n agentos svc/runtime 8000:8000 &
RUNTIME_PID=$!

# Wait for port forward
sleep 2

# Test health endpoint
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "runtime-service",
#   "timestamp": "2025-10-26T...",
#   "checks": {
#     "database": true,
#     "executor": true
#   }
# }

# View API docs
echo "API Docs: http://localhost:8000/docs"
```

## Step 8: Start Web UI

```bash
# In a new terminal window
cd services/web-ui

# Install dependencies (if not already done)
npm install

# Start dev server
npm run dev

# UI will be available at http://localhost:5173
```

## Step 9: Access the Application

Open your browser and navigate to:

**http://localhost:5173**

You should see:
- ✓ Sidebar with navigation
- ✓ Dashboard with stats and charts
- ✓ Deploy Agent page accessible

## Step 10: Test Agent Deployment

### Via UI:
1. Click "Deploy Agent" in sidebar
2. Enter Agent ID: `test-agent`
3. Enter Code:
   ```python
   result = input_data['x'] + input_data['y']
   ```
4. Select Max Memory: `512m`
5. Select Max CPU: `0.5`
6. Click "Deploy Agent"
7. Wait for success message

### Via API:
```bash
# Deploy agent
curl -X POST http://localhost:8000/api/v1/agents/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math-agent",
    "code": "result = input_data[\"x\"] + input_data[\"y\"]",
    "requirements": [],
    "environment": null,
    "max_memory": "512m",
    "max_cpu": "0.5"
  }'

# Invoke agent
curl -X POST http://localhost:8000/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math-agent",
    "input_data": {"x": 10, "y": 20},
    "timeout": 30
  }'

# Get agent status
curl http://localhost:8000/api/v1/agents/math-agent/status
```

## Troubleshooting

### PostgreSQL Not Ready
```bash
# Check PostgreSQL logs
kubectl logs -n agentos -l app=postgres --tail=50

# Restart PostgreSQL
kubectl rollout restart deployment/postgres -n agentos
```

### Runtime Service Not Starting
```bash
# Check pod status
kubectl get pods -n agentos -l app=runtime

# Check pod logs
kubectl logs -n agentos -l app=runtime --tail=100

# Describe pod for events
kubectl describe pod -n agentos -l app=runtime

# Common issues:
# 1. Secret not found - verify: kubectl get secrets -n agentos
# 2. Database not ready - check PostgreSQL first
# 3. Image not found - verify docker image exists
```

### UI Not Loading
```bash
# Check for errors in terminal
# Common issues:
# 1. Port 5173 already in use - kill process: lsof -ti:5173 | xargs kill -9
# 2. Node modules issue - rm -rf node_modules && npm install
# 3. Build errors - check console output
```

### Cannot Connect to Database
```bash
# Test database connection
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n agentos -- \
  psql -h postgres -U agentos -d agentos

# If connection fails:
# 1. Check PostgreSQL is running: kubectl get pods -n agentos
# 2. Check service exists: kubectl get svc -n agentos
# 3. Check secrets: kubectl get secrets -n agentos
```

### Port Forward Issues
```bash
# Kill all port forwards
pkill -f "kubectl port-forward"

# Restart port forwards
kubectl port-forward -n agentos svc/runtime 8000:8000 &
```

## Clean Up (if needed)

```bash
# Stop port forwards
pkill -f "kubectl port-forward"

# Delete namespace (removes all resources)
kubectl delete namespace agentos

# Or delete individual resources
kubectl delete -f k8s/08-runtime.yaml
kubectl delete deployment postgres -n agentos
kubectl delete svc postgres -n agentos
kubectl delete secret agentos-secrets -n agentos
```

## Quick Verification Commands

```bash
# Check all pods
kubectl get pods -n agentos

# Check all services
kubectl get svc -n agentos

# Check logs
kubectl logs -n agentos -l app=runtime --tail=20 -f

# Port forward (in background)
kubectl port-forward -n agentos svc/runtime 8000:8000 &

# Test health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Access UI
open http://localhost:5173
```

## Success Checklist

- [ ] Kubernetes cluster running
- [ ] Namespace `agentos` created
- [ ] Secrets configured
- [ ] PostgreSQL deployed and ready
- [ ] Database migration completed
- [ ] Runtime service deployed and healthy
- [ ] Port forwards active (8000 for runtime)
- [ ] UI running on port 5173
- [ ] Can access dashboard
- [ ] Can deploy an agent
- [ ] Can invoke an agent

## Next Steps

Once verified:
1. Test agent deployment via UI
2. Check dashboard updates
3. View invocations in dashboard table
4. Test agent invocation
5. Monitor logs and metrics

## Production Deployment

For production:
1. Use managed PostgreSQL (RDS, Cloud SQL)
2. Push Docker image to registry
3. Configure ingress for external access
4. Set up proper secrets management
5. Configure monitoring and logging
6. Set resource limits appropriately
7. Enable autoscaling
8. Set up backup and disaster recovery

---

**Ready to deploy!** Follow the steps above to get your Agent Economy OS running.
