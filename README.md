# Agent Economy OS

**Production-ready infrastructure for protocol-agnostic agent communication**

## Overview

Agent Economy OS provides a zero-trust, observable fabric for agents to discover, transact, and coordinate across protocols. This MVP delivers:

- **Cross-Agent Inference Fabric** with A2A and MCP protocol adapters
- **Decentralized Identity** using DIDs and Verifiable Credentials
- **Federated Memory** with vector search and tenant isolation
- **Policy Engine** with rate limiting and cost controls
- **Full Observability** with OpenTelemetry integration

## Architecture

```
┌─────────────────────────────────────────────────┐
│        External Clients (Agents, SDKs)          │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │   Kong Gateway     │
         └─────────┬──────────┘
                   │
    ┌──────────────▼───────────────┐
    │   Inference Fabric (Go)      │
    │   - Protocol Adapters        │
    │   - Router & Policy Enforce  │
    └──┬────────┬─────────┬────────┘
       │        │         │
   ┌───▼──┐ ┌──▼───┐ ┌──▼────┐
   │Identity│Memory│ │Policy │
   │(TypeScript)│(Python)│(Rust)│
   └───┬──┘ └──┬───┘ └──┬────┘
       │        │         │
   PostgreSQL Qdrant   Redis
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- kubectl & Helm 3
- Go 1.21+, Node 20+, Python 3.11+, Rust 1.70+

### Local Development

```bash
# Clone repository
git clone https://github.com/your-org/agent-economy-os.git
cd agent-economy-os

# Start infrastructure
./scripts/dev-setup.sh

# Access gateway
curl http://localhost:8080/health
```

### Register an Agent

```bash
# Create DID
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "task_executor",
    "metadata": {"name": "My Agent"}
  }'

# Issue credential
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subject_did": "did:agent:...",
    "claims": {"capabilities": ["execute"]},
    "expires_in": "30d"
  }'
```

### Invoke an Agent

```bash
curl -X POST http://localhost:8080/a2a/v1/invoke \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_did": "did:agent:caller",
    "target_did": "did:agent:target",
    "action": "execute",
    "params": {"task": "analyze"}
  }'
```

## Project Structure

```
agent-economy-os/
├── services/
│   ├── gateway/          # Go - Inference Fabric
│   ├── identity/         # TypeScript - DID/VC Management
│   ├── memory/           # Python - Federated Memory
│   └── policy-engine/    # Rust - Policy Evaluation
├── libraries/
│   └── sdk-typescript/   # Client SDK
├── infra/
│   ├── helm/            # Kubernetes deployments
│   └── migrations/      # Database schemas
└── scripts/             # Development tools
```

## Services

### Gateway Service (Port 8080)
- Protocol adapters (A2A, MCP)
- Intelligent routing
- Policy enforcement
- OpenTelemetry tracing

### Identity Service (Port 3000)
- DID registry and resolution
- Verifiable Credential issuance
- JWT token verification
- PostgreSQL storage

### Memory Service (Port 8000)
- Vector embeddings (Qdrant)
- Context management
- Tenant isolation
- Semantic search

### Policy Engine (Port 8081)
- Rate limiting (Redis-backed)
- Cost tracking
- Rule evaluation
- Sub-5ms latency

## Testing

```bash
# Gateway tests
cd services/gateway && go test -v ./...

# Identity tests
cd services/identity && npm test

# Memory tests
cd services/memory && pytest

# Policy engine tests
cd services/policy-engine && cargo test
```

## Deployment

```bash
# Build images
docker-compose -f docker-compose.dev.yaml build

# Deploy to Kubernetes
helm install gateway ./infra/helm/gateway --namespace agentos
helm install identity ./infra/helm/identity --namespace agentos
helm install memory ./infra/helm/memory --namespace agentos
helm install policy-engine ./infra/helm/policy-engine --namespace agentos
```

## Observability

- **Traces:** OpenTelemetry → ClickHouse
- **Metrics:** Prometheus + Grafana
- **Logs:** Structured JSON to stdout
- **Dashboards:** `/infra/helm/observability/dashboards/`

## SDK Usage

```typescript
import { AgentOSClient } from '@agentos/sdk';

const client = new AgentOSClient({
  apiUrl: 'https://api.agentos.io',
  agentDID: 'did:agent:my-agent',
  credential: 'eyJhbGc...',
});

const result = await client.invokeAgent(
  'did:agent:target',
  'execute',
  { task: 'hello' }
);
```

## Performance Targets

- **P99 Latency:** < 50ms (gateway)
- **Throughput:** 10,000 RPS per node
- **Availability:** 99.95% SLA
- **Error Rate:** < 0.1%

## Security

- Zero-trust architecture with mTLS (Istio)
- DID-based authentication
- Policy-based authorization
- Rate limiting and fraud detection
- All secrets in environment variables

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Write tests for new functionality
4. Ensure all tests pass (`./scripts/test-all.sh`)
5. Submit pull request

## License

Apache 2.0 - See LICENSE file

## Support

- Documentation: https://docs.agentos.io
- Issues: https://github.com/your-org/agent-economy-os/issues
- Discord: https://discord.gg/agentosos