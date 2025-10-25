# Kubernetes Deployment Guide - Agent Economy OS

Deploy the complete Agent Economy OS to your local Kubernetes cluster.

## Prerequisites

### Required

- **Kubernetes cluster** (Docker Desktop, Minikube, or Kind)
- **kubectl** configured and connected
- **Docker** for building images

### Optional

- **NGINX Ingress Controller** for domain-based access
- **metrics-server** for HPA autoscaling

## Quick Deploy (One Command)

```bash
cd /Users/upalc/AgentOS/agentos
./scripts/deploy-local-k8s.sh
```

This script will:
1. Build all Docker images
2. Create namespace and configs
3. Deploy databases (PostgreSQL, Redis, Qdrant, ClickHouse)
4. Deploy services (Gateway, Identity, Memory, Policy Engine, Web UI)
5. Configure ingress

## Manual Steps

### 1. Build Images

```bash
cd /Users/upalc/AgentOS/agentos
./scripts/build-images.sh
```

### 2. Apply Manifests

```bash
cd /Users/upalc/AgentOS/agentos

# Infrastructure
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/postgres-init-configmap.yaml

# Databases (with persistent storage)
kubectl apply -f k8s/03-postgres.yaml
kubectl apply -f k8s/04-redis.yaml
kubectl apply -f k8s/05-qdrant.yaml
kubectl apply -f k8s/06-clickhouse.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n agentos --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n agentos --timeout=300s
kubectl wait --for=condition=ready pod -l app=qdrant -n agentos --timeout=300s

# Application services
kubectl apply -f k8s/07-identity.yaml
kubectl apply -f k8s/08-memory.yaml
kubectl apply -f k8s/09-policy-engine.yaml
kubectl apply -f k8s/10-gateway.yaml
kubectl apply -f k8s/11-web-ui.yaml
kubectl apply -f k8s/12-ingress.yaml
```

### 3. Verify

```bash
kubectl get pods -n agentos
kubectl get svc -n agentos
```

### 4. Access Application

**Option A: Ingress (requires DNS)**
```bash
# Add to /etc/hosts
echo "127.0.0.1 agentos.local" | sudo tee -a /etc/hosts

# Access at http://agentos.local
```

**Option B: Port Forward**
```bash
kubectl port-forward -n agentos svc/web-ui 3001:80
kubectl port-forward -n agentos svc/gateway 8080:8080

# Access at http://localhost:3001
```

## Service Details

| Service | Replicas | Resources | Port |
|---------|----------|-----------|------|
| PostgreSQL | 1 | 256Mi-1Gi, 250m-1000m | 5432 |
| Redis | 1 | 128Mi-512Mi, 100m-500m | 6379 |
| Qdrant | 1 | 512Mi-2Gi, 250m-1000m | 6333 |
| ClickHouse | 1 | 512Mi-2Gi, 250m-1000m | 8123 |
| Identity | 2 | 256Mi-1Gi, 250m-1000m | 3000 |
| Memory | 2 | 512Mi-2Gi, 500m-2000m | 8000 |
| Policy Engine | 3 | 128Mi-512Mi, 250m-1000m | 8081 |
| Gateway | 3 (HPA: 3-10) | 256Mi-1Gi, 250m-1000m | 8080 |
| Web UI | 2 | 128Mi-256Mi, 100m-500m | 80 |

## Monitoring

```bash
# Watch all pods
kubectl get pods -n agentos -w

# Check logs
kubectl logs -n agentos -l app=gateway --tail=50 -f

# Describe a specific pod
kubectl describe pod -n agentos <pod-name>

# Check HPA status
kubectl get hpa -n agentos

# View persistent volumes
kubectl get pvc -n agentos
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -n agentos <pod-name>

# Check logs
kubectl logs -n agentos <pod-name>

# Check if images exist
docker images | grep agentos
```

### Database Connection Issues

```bash
# Test PostgreSQL
kubectl exec -it -n agentos deployment/postgres -- psql -U postgres -d agentos -c "SELECT 1"

# Test Redis
kubectl exec -it -n agentos deployment/redis -- redis-cli -a changeme456 PING
```

### Image Pull Errors

Make sure images are built and available:
```bash
# Rebuild images
./scripts/build-images.sh

# For Minikube, load images
minikube image load agentos/gateway:0.1.0
minikube image load agentos/identity:0.1.0
minikube image load agentos/memory:0.1.0
minikube image load agentos/policy-engine:0.1.0
minikube image load agentos/web-ui:0.1.0
```

## Scaling

```bash
# Manual scaling
kubectl scale deployment -n agentos gateway --replicas=5

# Check HPA
kubectl get hpa -n agentos gateway-hpa

# Update HPA
kubectl autoscale deployment -n agentos gateway --cpu-percent=70 --min=3 --max=10
```

## Updating Services

```bash
# Rebuild image
cd services/gateway
docker build -t agentos/gateway:0.1.1 .

# Update deployment
kubectl set image deployment/gateway -n agentos gateway=agentos/gateway:0.1.1

# Rollback if needed
kubectl rollout undo deployment/gateway -n agentos
```

## Cleanup

### Delete Specific Components

```bash
# Delete services only (keep databases)
kubectl delete deployment -n agentos gateway identity memory policy-engine web-ui

# Delete everything except PVCs
kubectl delete -f k8s/ --ignore-not-found=true
```

### Complete Cleanup

```bash
# Delete namespace (removes everything including PVCs)
kubectl delete namespace agentos
```
