# Quick Deployment Guide

## Prerequisites

- Docker Desktop or Docker Engine
- Kubernetes cluster (local or cloud)
- kubectl configured
- Helm 3.x installed

## Option 1: Local Development (Docker Compose)

**Fastest way to get started:**

```bash
# Start all services locally
./scripts/dev-setup.sh

# Verify services are running
curl http://localhost:8080/health
curl http://localhost:3000/health
curl http://localhost:8000/health
curl http://localhost:8081/health

# View logs
docker-compose -f docker-compose.dev.yaml logs -f
```

## Option 2: Kubernetes Deployment

### Step 1: Build Images

```bash
# Build all Docker images
./scripts/build-images.sh

# If using a remote registry, push images
export REGISTRY=your-registry.io/agentos
docker push $REGISTRY/gateway:0.1.0
docker push $REGISTRY/identity:0.1.0
docker push $REGISTRY/memory:0.1.0
docker push $REGISTRY/policy-engine:0.1.0
```

### Step 2: Configure Secrets

Edit `infra/k8s/secrets.yaml` and update:
- Database password
- Redis password  
- Issuer private key (generate with `jose` library)

### Step 3: Deploy to Kubernetes

```bash
# Deploy everything
./scripts/deploy-k8s.sh

# Or deploy manually:
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/secrets.yaml

# Deploy services
helm install gateway ./infra/helm/gateway --namespace agentos
helm install identity ./infra/helm/identity --namespace agentos
helm install memory ./infra/helm/memory --namespace agentos
helm install policy-engine ./infra/helm/policy-engine --namespace agentos
```

### Step 4: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n agentos

# Check services
kubectl get svc -n agentos

# View gateway logs
kubectl logs -n agentos -l app=gateway --tail=50
```

### Step 5: Access the API

```bash
# Port forward to access locally
kubectl port-forward -n agentos svc/gateway 8080:8080

# Test the gateway
curl http://localhost:8080/health
```

## Quick Test Flow

### 1. Create a DID

```bash
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agentType": "assistant",
    "metadata": {"name": "Test Agent"}
  }'
```

Save the returned DID: `did:agent:abc-123...`

### 2. Issue a Credential

```bash
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subjectDID": "did:agent:abc-123...",
    "claims": {"capabilities": ["execute"]},
    "expiresIn": "30d"
  }'
```

Save the returned JWT credential.

### 3. Invoke an Agent

```bash
curl -X POST http://localhost:8080/a2a/v1/invoke \
  -H "Authorization: Bearer YOUR_JWT_CREDENTIAL" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_did": "did:agent:abc-123...",
    "target_did": "did:agent:target",
    "action": "execute",
    "params": {"task": "hello"}
  }'
```

## Monitoring

### View Metrics

```bash
# Prometheus metrics from gateway
curl http://localhost:8080/metrics

# Or via Kubernetes
kubectl port-forward -n agentos svc/gateway 8080:8080
```

### Check Database

```bash
# Connect to PostgreSQL
kubectl exec -it -n agentos postgres-0 -- psql -U agentos

# List DIDs
SELECT id, document->>'metadata' FROM dids;

# List credentials
SELECT subject_did, issued_at FROM credentials;
```

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod -n agentos <pod-name>
kubectl logs -n agentos <pod-name>
```

### Database Connection Issues

```bash
# Check PostgreSQL is ready
kubectl exec -n agentos postgres-0 -- pg_isready

# Verify secrets
kubectl get secret -n agentos agentos-secrets -o yaml
```

### Service Discovery Issues

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -n agentos -- nslookup identity
```

## Scaling

```bash
# Scale gateway
kubectl scale deployment -n agentos gateway --replicas=5

# Enable autoscaling (already configured in Helm)
kubectl get hpa -n agentos
```

## Cleanup

### Docker Compose

```bash
docker-compose -f docker-compose.dev.yaml down -v
```

### Kubernetes

```bash
# Remove application
helm uninstall gateway identity memory policy-engine -n agentos

# Remove namespace (WARNING: deletes everything)
kubectl delete namespace agentos
```

## Production Considerations

Before deploying to production:

1. **Update Secrets**: Use proper key generation for issuer keys
2. **Configure Ingress**: Set up your domain in `infra/helm/gateway/values.yaml`
3. **Enable TLS**: Install cert-manager and configure certificates
4. **Set Resource Limits**: Review and adjust CPU/memory in values.yaml
5. **Configure Backups**: Set up database backup jobs
6. **Enable Monitoring**: Install Prometheus/Grafana stack
7. **Review Security**: Run security scans on images

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full production setup guide.

## Support

- Documentation: [docs/](docs/)
- API Reference: [docs/API.md](docs/API.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
