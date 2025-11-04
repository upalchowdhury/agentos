# AgentOS Production Deployment Guide
**Fine-Grained Multi-Agent Span-Level Observability**

Version: 1.0.0
Last Updated: 2025-11-03

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Database Setup](#database-setup)
5. [Service Deployment](#service-deployment)
6. [Model B SDK Deployment](#model-b-sdk-deployment)
7. [Gateway Configuration](#gateway-configuration)
8. [UI Deployment](#ui-deployment)
9. [Monitoring & Observability](#monitoring--observability)
10. [Security Hardening](#security-hardening)
11. [Performance Tuning](#performance-tuning)
12. [Troubleshooting](#troubleshooting)
13. [Runbook](#runbook)

---

## Overview

This guide covers the complete production deployment of AgentOS with **fine-grained span-level observability** for multi-agent systems, including:

✅ **Span-level telemetry** - Hierarchical spans for prompts, tools, sub-agents
✅ **Inter-agent edge tracking** - A2A/MCP communication flows
✅ **W3C trace context propagation** - traceparent/baggage headers
✅ **Flamegraph visualization** - Hierarchical span explorer
✅ **Sequence diagrams** - Inter-agent communication flows
✅ **Anomaly detection** - Prompt injection, tool abuse, cost outliers
✅ **Model B SDK** - External agent instrumentation
✅ **Deterministic replay** - Span-level reproduction

---

## Prerequisites

### Infrastructure
- **Kubernetes Cluster**: v1.24+ (or Docker Compose for local)
- **PostgreSQL**: v14+ with UUID extension
- **Redis**: v7+ (optional, for caching)
- **Object Storage**: S3/MinIO for artifacts
- **Load Balancer**: NGINX/Envoy/Traefik

### Tools
- `kubectl` v1.24+
- `helm` v3.10+
- `docker` v20.10+
- `psql` (PostgreSQL client)
- `python` 3.10+ (for SDK testing)
- `go` 1.21+ (for gateway)

### Access
- Container registry access (Docker Hub / ECR / GCR)
- Domain with DNS control
- TLS certificates (Let's Encrypt recommended)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                   (NGINX / Envoy / Traefik)                  │
└────────────────────┬─────────────────┬──────────────────────┘
                     │                 │
         ┌───────────▼────────┐   ┌────▼─────────────┐
         │   Gateway Service   │   │   Web UI (React) │
         │   (Go + OTel)       │   └──────────────────┘
         │  - Trace Context    │
         │  - Edge Tracking    │
         │  - Policy Enforce   │
         └──────────┬──────────┘
                    │
        ┌───────────┴────────────┬─────────────────────┐
        │                        │                     │
┌───────▼────────┐  ┌────────────▼──────┐  ┌──────────▼──────────┐
│ Runtime Service│  │ Observability Svc │  │  Identity Service   │
│ (Python/FastAPI)│  │  (Span APIs)      │  │  (DID-based auth)   │
│ - Model A exec │  │  - Span ingest    │  └─────────────────────┘
│ - Model B proxy│  │  - Edge APIs      │
│ - Span recorder│  │  - Anomaly detect │
└────────┬───────┘  └───────────────────┘
         │
┌────────▼────────────────────────────────────────────────┐
│                    PostgreSQL Database                   │
│  - agents, invocations, agent_versions                  │
│  - telemetry_spans, telemetry_edges                     │
│  - span_links, span_anomalies                           │
│  - trace_context, cost_snapshots                        │
└──────────────────────────────────────────────────────────┘
```

---

## Database Setup

### Step 1: Run Migrations

```bash
# Navigate to migrations directory
cd /Users/upalc/AgentOS/agentos/infra/migrations

# Run migrations in order
psql -h localhost -U agentos -d agentos_prod -f 005_enhanced_runtime_schema.sql
psql -h localhost -U agentos -d agentos_prod -f 006_span_level_observability.sql

# Verify tables created
psql -h localhost -U agentos -d agentos_prod -c "\dt"
```

Expected tables:
- `agents`
- `agent_versions`
- `invocations`
- `cost_snapshots`
- `agent_tokens`
- `pricing_config`
- **`telemetry_spans`** ✓
- **`telemetry_edges`** ✓
- **`span_links`** ✓
- **`span_anomalies`** ✓
- **`trace_context`** ✓

### Step 2: Create Indexes

```sql
-- Additional performance indexes
CREATE INDEX CONCURRENTLY idx_spans_trace_agent
  ON telemetry_spans(trace_id, agent_id, start_ts DESC);

CREATE INDEX CONCURRENTLY idx_edges_trace_time
  ON telemetry_edges(trace_id, timestamp ASC);

CREATE INDEX CONCURRENTLY idx_anomalies_open
  ON span_anomalies(agent_id, status) WHERE status = 'open';
```

### Step 3: Configure Connection Pool

```yaml
# config/database.yaml
database:
  host: postgres.agentos.svc.cluster.local
  port: 5432
  name: agentos_prod
  user: agentos
  password: ${DB_PASSWORD}
  pool:
    min_size: 10
    max_size: 100
    timeout: 30
    max_lifetime: 3600
```

---

## Service Deployment

### Runtime Service

```bash
# Build Docker image
cd services/runtime
docker build -t agentos/runtime:v1.0.0 .

# Push to registry
docker push agentos/runtime:v1.0.0

# Deploy to Kubernetes
kubectl apply -f infra/k8s/runtime-deployment.yaml
```

**Key Environment Variables:**
```yaml
env:
  - name: DATABASE_URL
    value: postgresql://agentos:${DB_PASSWORD}@postgres:5432/agentos_prod
  - name: SPAN_INGESTION_ENABLED
    value: "true"
  - name: ANOMALY_DETECTION_ENABLED
    value: "true"
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: http://otel-collector:4318
```

### Gateway Service

```bash
# Build gateway
cd services/gateway
go build -o gateway ./cmd/server

# Build Docker image
docker build -t agentos/gateway:v1.0.0 .
docker push agentos/gateway:v1.0.0

# Deploy
kubectl apply -f infra/k8s/gateway-deployment.yaml
```

**Gateway Configuration:**
```yaml
# config/gateway.yaml
gateway:
  port: 8080
  runtime_api_url: http://runtime:8000
  identity_api_url: http://identity:8001

  trace_context:
    enabled: true
    edge_tracking: true
    propagation: w3c

  middleware:
    - trace_context
    - policy_enforcement
    - rate_limiting
```

### Observability Service

```bash
# Deploy span APIs
cd services/observability
docker build -t agentos/observability:v1.0.0 .
docker push agentos/observability:v1.0.0

kubectl apply -f infra/k8s/observability-deployment.yaml
```

---

## Model B SDK Deployment

### Step 1: Publish SDK to PyPI

```bash
cd sdks/python

# Update version
echo "0.1.0" > agentos_sdk/version.py

# Build distribution
python setup.py sdist bdist_wheel

# Publish to PyPI
twine upload dist/*
```

### Step 2: Install in External Agents

```bash
# External agents install SDK
pip install agentos-sdk==0.1.0
```

### Step 3: Instrument Agent Code

```python
# external_agent.py
from agentos_sdk import AgentOSClient

client = AgentOSClient(
    api_url="https://api.agentos.example.com",
    api_key="your-api-key",
    agent_id="external-agent-123"
)

@client.instrument()
def my_agent(input_data):
    with client.trace_invocation(input_data) as recorder:
        # Create spans
        with recorder.create_span("preprocess", "system") as span:
            result = preprocess(input_data)
            span.set_io(input_data, result)

        # Track model calls
        with recorder.create_span("model.call", "prompt") as span:
            span.set_model("openai", "gpt-4o", {"temperature": 0.7})
            output = call_llm(result)
            span.set_io(result, output, tokens_in=100, tokens_out=50)
            span.set_cost(5)

        return output
```

### Step 4: Verify Telemetry

```bash
# Check spans ingested
curl -H "Authorization: Bearer ${API_KEY}" \
  https://api.agentos.example.com/v1/spans/trace/${TRACE_ID}

# Verify "Verified Telemetry" badge
curl https://api.agentos.example.com/v1/catalog/agents/external-agent-123
```

---

## Gateway Configuration

### Enable Trace Context Middleware

```go
// services/gateway/cmd/server/main.go
import (
    "github.com/agentos/gateway/internal/middleware"
)

func main() {
    router := gin.Default()

    // Add trace context middleware
    traceMiddleware := middleware.NewTraceContextMiddleware(
        "http://runtime:8000"
    )
    router.Use(traceMiddleware.Handler)

    // ... rest of setup
}
```

### Configure OTel Collector

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  prometheus:
    endpoint: ":8889"

  logging:
    loglevel: info

  otlp/grafana:
    endpoint: grafana-tempo:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging, otlp/grafana]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

---

## UI Deployment

### Build Web UI

```bash
cd services/web-ui

# Install dependencies
npm install

# Add new components to router
# src/App.tsx
import SpanFlamegraph from './components/SpanFlamegraph';
import SequenceDiagram from './components/SequenceDiagram';

# Build production bundle
npm run build

# Build Docker image
docker build -t agentos/web-ui:v1.0.0 .
docker push agentos/web-ui:v1.0.0
```

### Deploy to Kubernetes

```yaml
# infra/k8s/web-ui-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-ui
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-ui
  template:
    metadata:
      labels:
        app: web-ui
    spec:
      containers:
      - name: web-ui
        image: agentos/web-ui:v1.0.0
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: https://api.agentos.example.com
---
apiVersion: v1
kind: Service
metadata:
  name: web-ui
spec:
  selector:
    app: web-ui
  ports:
  - port: 80
    targetPort: 3000
```

---

## Monitoring & Observability

### Grafana Dashboards

**Import Pre-Built Dashboards:**

1. **Span Performance Dashboard**
   - Span count by kind/status
   - P50/P95/P99 latencies
   - Error rates
   - Cost trends

2. **Inter-Agent Flow Dashboard**
   - Edge count by protocol
   - Signature verification rate
   - Policy enforcement metrics
   - A2A communication heatmap

3. **Anomaly Dashboard**
   - Open anomalies by type/severity
   - Detection rate trends
   - False positive rates
   - MTTR (Mean Time To Resolution)

### Prometheus Metrics

```yaml
# Key metrics to monitor
- agentos_spans_total{kind, status}
- agentos_span_duration_seconds{kind, quantile}
- agentos_edges_total{channel, verified}
- agentos_anomalies_total{type, severity}
- agentos_span_cost_cents{agent_id}
```

### Alerting Rules

```yaml
# alerts.yaml
groups:
- name: agentos_spans
  rules:
  - alert: HighSpanErrorRate
    expr: rate(agentos_spans_total{status="error"}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High span error rate detected"

  - alert: CriticalAnomaly
    expr: agentos_anomalies_total{severity="critical", status="open"} > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Critical anomaly detected"
```

---

## Security Hardening

### 1. Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: runtime-policy
spec:
  podSelector:
    matchLabels:
      app: runtime
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 2. TLS Everywhere

- Gateway → Runtime: mTLS
- Runtime → Database: TLS 1.3
- External API: Let's Encrypt certs

### 3. Secrets Management

```bash
# Use Kubernetes secrets
kubectl create secret generic agentos-secrets \
  --from-literal=db-password=${DB_PASSWORD} \
  --from-literal=api-key=${API_KEY}

# Mount in pods
volumes:
- name: secrets
  secret:
    secretName: agentos-secrets
```

---

## Performance Tuning

### Database Optimization

```sql
-- Partition large tables
CREATE TABLE telemetry_spans_2025_11 PARTITION OF telemetry_spans
  FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Vacuum and analyze
VACUUM ANALYZE telemetry_spans;
VACUUM ANALYZE telemetry_edges;

-- Autovacuum tuning
ALTER TABLE telemetry_spans SET (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);
```

### Application Tuning

```yaml
# Runtime service
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"

# Database connection pool
pool:
  min_size: 20
  max_size: 200
  statement_cache_size: 1000
```

### Caching Strategy

```python
# Cache span stats
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_agent_span_stats(agent_id: str, ttl_seconds=300):
    return db.fetch("SELECT * FROM span_stats_per_agent WHERE agent_id = $1", agent_id)
```

---

## Troubleshooting

### Spans Not Appearing

**Check span ingestion:**
```bash
# Check logs
kubectl logs -f deployment/runtime | grep "span"

# Verify database
psql -c "SELECT COUNT(*) FROM telemetry_spans WHERE created_at > NOW() - INTERVAL '1 hour';"
```

**Common issues:**
- Missing `trace_id` in span data
- Database connection pool exhausted
- OPA policy blocking ingestion

### Edges Not Tracked

**Check gateway middleware:**
```bash
# Verify middleware active
curl -v https://api.agentos.example.com/health

# Check headers
traceparent: 00-...
baggage: agent_id=...,version_id=...
```

**Common issues:**
- Gateway not proxying A2A calls
- Edge tracker failing silently
- Target agent ID extraction failing

### Flamegraph Not Loading

**Check API response:**
```bash
curl -H "Authorization: Bearer ${TOKEN}" \
  https://api.agentos.example.com/v1/spans/trace/${TRACE_ID}
```

**Common issues:**
- Circular parent-child relationships
- Missing span depth calculation
- CORS issues

---

## Runbook

### Daily Operations

**Morning Checks (Automated):**
```bash
# Check service health
kubectl get pods -n agentos

# Check database size
psql -c "SELECT pg_size_pretty(pg_database_size('agentos_prod'));"

# Check open anomalies
psql -c "SELECT COUNT(*) FROM span_anomalies WHERE status = 'open';"
```

**Weekly Maintenance:**
- Review anomaly trends
- Archive old spans (>90 days)
- Update SDK versions
- Review cost efficiency

### Incident Response

**High Span Error Rate:**
1. Check gateway logs for policy denials
2. Review recent deployments
3. Check external API status
4. Investigate failing agents via flamegraph

**Critical Anomaly Alert:**
1. Query anomaly details:
   ```sql
   SELECT * FROM span_anomalies
   WHERE severity = 'critical' AND status = 'open'
   ORDER BY detected_at DESC LIMIT 10;
   ```
2. Review evidence in span detail panel
3. Replay span if needed
4. Update policies if false positive
5. Mark as resolved with notes

---

## Success Metrics

After deployment, monitor these KPIs:

✅ **Span Coverage:** ≥95% of invocations have spans
✅ **Edge Fidelity:** ≥99% of A2A calls tracked
✅ **Telemetry Quality:** ≥70% agents with "Verified" badge
✅ **Anomaly MTTR:** <10 minutes
✅ **Replay Success:** ≥90% spans reproducible
✅ **UI Load Time:** Flamegraph <2s, Sequence diagram <1.5s

---

## Next Steps

1. **Week 1:** Deploy database + runtime + gateway
2. **Week 2:** Deploy web UI with flamegraph/sequence diagram
3. **Week 3:** Publish Model B SDK, onboard external agents
4. **Week 4:** Enable anomaly detection, tune alerts
5. **Ongoing:** Monitor KPIs, iterate based on feedback

---

**Questions? Issues?**
- GitHub: https://github.com/agentos/agentos/issues
- Docs: https://docs.agentos.example.com
- Slack: #agentos-support

**End of Guide**
