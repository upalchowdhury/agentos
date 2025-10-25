# Deployment Guide

## Prerequisites

- Kubernetes cluster (1.27+)
- Helm 3.x
- kubectl configured
- Container registry access

## Infrastructure Setup

### 1. Create Namespace

```bash
kubectl create namespace agentos
kubectl config set-context --current --namespace=agentos
```

### 2. Deploy PostgreSQL

```bash
helm install postgres bitnami/postgresql \
  --set auth.database=agentos \
  --set auth.username=agentos \
  --set auth.password=CHANGE_ME \
  --set primary.persistence.size=50Gi \
  --set metrics.enabled=true
```

### 3. Deploy Redis

```bash
helm install redis bitnami/redis \
  --set architecture=standalone \
  --set auth.enabled=true \
  --set auth.password=CHANGE_ME \
  --set master.persistence.size=10Gi
```

### 4. Deploy Qdrant

```bash
helm install qdrant qdrant/qdrant \
  --set persistence.size=100Gi \
  --set resources.requests.memory=2Gi
```

### 5. Deploy ClickHouse

```bash
helm install clickhouse bitnami/clickhouse \
  --set auth.username=agentos \
  --set auth.password=CHANGE_ME \
  --set persistence.size=100Gi
```

## Application Deployment

### 1. Build and Push Images

```bash
# Set your registry
export REGISTRY=your-registry.io/agentos

# Build all services
make build

# Tag and push
docker tag agentos/gateway:latest $REGISTRY/gateway:0.1.0
docker tag agentos/identity:latest $REGISTRY/identity:0.1.0
docker tag agentos/memory:latest $REGISTRY/memory:0.1.0
docker tag agentos/policy-engine:latest $REGISTRY/policy-engine:0.1.0

docker push $REGISTRY/gateway:0.1.0
docker push $REGISTRY/identity:0.1.0
docker push $REGISTRY/memory:0.1.0
docker push $REGISTRY/policy-engine:0.1.0
```

### 2. Create Secrets

```bash
kubectl create secret generic agentos-secrets \
  --from-literal=database-url="postgresql://agentos:PASSWORD@postgres:5432/agentos" \
  --from-literal=redis-password="PASSWORD" \
  --from-literal=issuer-private-key='{"kty":"OKP",...}'
```

### 3. Run Migrations

```bash
kubectl run -i --rm --restart=Never migrate \
  --image=postgres:16-alpine \
  -- psql postgresql://agentos:PASSWORD@postgres:5432/agentos \
  < infra/migrations/001_initial_schema.sql
```

### 4. Deploy Services

```bash
# Identity Service
helm install identity ./infra/helm/identity \
  --set image.repository=$REGISTRY/identity \
  --set image.tag=0.1.0

# Memory Service
helm install memory ./infra/helm/memory \
  --set image.repository=$REGISTRY/memory \
  --set image.tag=0.1.0

# Policy Engine
helm install policy-engine ./infra/helm/policy-engine \
  --set image.repository=$REGISTRY/policy-engine \
  --set image.tag=0.1.0

# Gateway
helm install gateway ./infra/helm/gateway \
  --set image.repository=$REGISTRY/gateway \
  --set image.tag=0.1.0 \
  --set ingress.hosts[0].host=api.yourdomain.com
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# Check logs
kubectl logs -l app=gateway --tail=50
```

## Ingress Configuration

### Install Ingress Controller

```bash
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --set controller.metrics.enabled=true \
  --set controller.podAnnotations."prometheus\.io/scrape"=true
```

### Install Cert Manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Monitoring Setup

### Prometheus & Grafana

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=CHANGE_ME
```

Access Grafana:
```bash
kubectl port-forward svc/prometheus-grafana 3000:80
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment gateway --replicas=5
kubectl scale deployment identity --replicas=3
```

### Auto-scaling

HPA is configured automatically via Helm values. Verify:

```bash
kubectl get hpa
```

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
kubectl exec -i postgres-0 -- pg_dump -U agentos agentos > backup.sql

# Restore
kubectl exec -i postgres-0 -- psql -U agentos agentos < backup.sql
```

### Qdrant Snapshots

```bash
# Create snapshot
curl -X POST http://qdrant:6333/collections/agent_memories/snapshots

# List snapshots
curl http://qdrant:6333/collections/agent_memories/snapshots
```

## Upgrade Process

### Rolling Update

```bash
# Update image tag
helm upgrade gateway ./infra/helm/gateway \
  --set image.tag=0.2.0 \
  --reuse-values

# Watch rollout
kubectl rollout status deployment/gateway
```

### Rollback

```bash
helm rollback gateway
```

## Troubleshooting

### Pod Not Starting

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --previous
```

### Database Connection Issues

```bash
# Test connection
kubectl run -i --rm --restart=Never psql-test \
  --image=postgres:16-alpine \
  -- psql postgresql://agentos:PASSWORD@postgres:5432/agentos -c "SELECT 1"
```

### Service Discovery Issues

```bash
# Check DNS
kubectl run -i --rm --restart=Never dns-test \
  --image=busybox \
  -- nslookup identity
```

## Production Checklist

- [ ] Resource limits configured
- [ ] HPA enabled and tested
- [ ] Secrets properly secured
- [ ] TLS certificates valid
- [ ] Monitoring dashboards created
- [ ] Alerting rules configured
- [ ] Backup jobs scheduled
- [ ] Disaster recovery tested
- [ ] Load testing completed
- [ ] Security scan passed
