# Quick Start Guide

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2.0+
- (Optional) kubectl and Helm for Kubernetes deployment

## Local Development Setup

### 1. Start the Platform

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start all services
./scripts/dev-setup.sh
```

This will:
- Start PostgreSQL, Redis, Qdrant, and ClickHouse
- Run database migrations
- Start Gateway, Identity, Memory, and Policy Engine services

### 2. Verify Services

```bash
# Check all services are healthy
docker-compose -f docker-compose.dev.yaml ps

# Test Gateway
curl http://localhost:8080/health
```

## Create Your First Agent

### 1. Create a DID (Decentralized Identifier)

```bash
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agentType": "assistant",
    "metadata": {
      "name": "My First Agent",
      "description": "A helpful assistant"
    }
  }'
```

Response:
```json
{
  "did": {
    "id": "did:agent:abc-123-...",
    "@context": ["https://www.w3.org/ns/did/v1"],
    ...
  }
}
```

### 2. Issue a Credential

```bash
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subjectDID": "did:agent:abc-123-...",
    "claims": {
      "capabilities": ["execute", "read", "write"],
      "role": "assistant"
    },
    "expiresIn": "30d"
  }'
```

Response:
```json
{
  "credential": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Invoke Another Agent

```bash
curl -X POST http://localhost:8080/a2a/v1/invoke \
  -H "Authorization: Bearer YOUR_JWT_CREDENTIAL" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_did": "did:agent:caller-id",
    "target_did": "did:agent:target-id",
    "action": "execute",
    "params": {
      "task": "analyze_data",
      "data": ["item1", "item2"]
    },
    "conversation_id": "conv-12345"
  }'
```

## Using the SDK

### TypeScript/JavaScript

```bash
npm install @agentos/sdk
```

```typescript
import { AgentOSClient } from '@agentos/sdk';

const client = new AgentOSClient({
  apiUrl: 'http://localhost:8080',
  agentDID: 'did:agent:your-agent-id',
  credential: 'your-jwt-credential',
});

// Invoke another agent
const result = await client.invokeAgent({
  targetDID: 'did:agent:target',
  action: 'execute',
  params: { task: 'hello' },
});

// Store memory
const memoryId = await client.storeMemory(
  'User asked about pricing',
  'conv-123',
  { topic: 'pricing' }
);

// Search memories
const memories = await client.searchMemories(
  'pricing information',
  'conv-123',
  10
);
```

## Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yaml logs -f

# Specific service
docker-compose -f docker-compose.dev.yaml logs -f gateway
```

### Prometheus Metrics

Available at: http://localhost:8889/metrics

### Database Access

```bash
# PostgreSQL
docker-compose -f docker-compose.dev.yaml exec postgres psql -U postgres -d agentos

# Redis
docker-compose -f docker-compose.dev.yaml exec redis redis-cli
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yaml logs

# Restart services
docker-compose -f docker-compose.dev.yaml restart

# Clean restart
docker-compose -f docker-compose.dev.yaml down -v
./scripts/dev-setup.sh
```

### Port Conflicts

If ports are already in use, modify `docker-compose.dev.yaml` to use different ports.

### Database Connection Issues

```bash
# Check PostgreSQL is ready
docker-compose -f docker-compose.dev.yaml exec postgres pg_isready -U postgres

# Re-run migrations
docker-compose -f docker-compose.dev.yaml exec postgres psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/001_initial_schema.sql
```

## Next Steps

- Read the [Architecture Guide](./ARCHITECTURE.md)
- Explore [API Documentation](./API.md)
- Deploy to [Kubernetes](./KUBERNETES.md)
- Learn about [Security Best Practices](./SECURITY.md)
