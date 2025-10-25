# Architecture Overview

## System Design

Agent Economy OS is a microservices-based platform for protocol-agnostic agent communication, built with zero-trust security and full observability.

## Core Services

### Gateway Service (Go)
**Responsibilities:**
- Protocol adaptation (A2A, MCP)
- Request routing
- Authentication verification
- Policy enforcement
- OpenTelemetry tracing

**Technology:**
- Language: Go 1.21+
- Framework: Gorilla Mux
- Performance: <5ms p99 latency
- Scale: 10,000 RPS per node

**Key Components:**
- `internal/router`: Intelligent request routing
- `internal/adapters`: Protocol implementations
- `internal/middleware`: Auth, logging, tracing
- `pkg/types`: Shared type definitions

### Identity Service (TypeScript)
**Responsibilities:**
- DID creation and resolution
- Verifiable Credential issuance
- JWT token verification
- Credential revocation

**Technology:**
- Language: TypeScript/Node.js 20+
- Framework: Express
- Storage: PostgreSQL
- Crypto: jose library (EdDSA)

**Key Components:**
- `did/registry`: DID document management
- `credentials/issuer`: VC issuance
- `credentials/verifier`: VC verification

### Memory Service (Python)
**Responsibilities:**
- Vector embeddings
- Semantic search
- Context management
- Tenant isolation

**Technology:**
- Language: Python 3.11+
- Framework: FastAPI
- Vector DB: Qdrant
- Embeddings: SentenceTransformers
- Storage: PostgreSQL + Qdrant

**Key Components:**
- `vector_store`: Embedding and search
- `context_manager`: Memory lifecycle
- `isolation`: Access control

### Policy Engine (Rust)
**Responsibilities:**
- Rate limiting
- Cost tracking
- Rule evaluation
- Sub-5ms response time

**Technology:**
- Language: Rust 1.75+
- Framework: Actix-web
- Cache: Redis
- Performance: <5ms latency

**Key Components:**
- `engine`: Policy evaluation logic
- `rules`: Rule definitions
- Redis integration for state

## Data Flow

### Agent Invocation Flow
```
1. Client → Gateway (with JWT credential)
2. Gateway → Identity Service (verify credential)
3. Gateway → Policy Engine (check limits)
4. Gateway → Memory Service (fetch context)
5. Gateway → Target Agent (execute)
6. Gateway → Memory Service (store interaction)
7. Gateway → Client (return response)
```

### Authentication Flow
```
1. Agent → Identity Service (create DID)
2. Identity Service → PostgreSQL (store DID document)
3. Agent → Identity Service (issue credential)
4. Identity Service → PostgreSQL (store credential)
5. Agent → Gateway (with JWT)
6. Gateway → Identity Service (verify JWT)
```

## Database Schema

### PostgreSQL Tables
- `dids`: DID documents and metadata
- `credentials`: Issued credentials and revocation status
- `memories`: Text content and metadata
- `interactions`: Audit log of agent calls
- `tenant_access`: Access control rules
- `cost_events`: Cost tracking events

### Qdrant Collections
- `agent_memories`: Vector embeddings (384 dimensions)

### Redis Keys
- `rate_limit:{did}:{window}`: Request counters
- `cost_limit:{did}:{window}`: Cost accumulation

## Security Architecture

### Zero-Trust Principles
1. **No Implicit Trust**: Every request verified
2. **DID-Based Identity**: Decentralized identifiers
3. **Verifiable Credentials**: Cryptographic proof
4. **Policy Enforcement**: Rate limits and cost controls
5. **Tenant Isolation**: Strict data separation

### Authentication Chain
```
JWT Token → EdDSA Signature → DID Document → Public Key → Verification
```

### Authorization Layers
1. **Identity**: Valid credential?
2. **Policy**: Within limits?
3. **Tenant**: Access to resource?

## Observability

### Traces (OpenTelemetry)
- Distributed tracing across services
- Span attributes: agent DIDs, actions, costs
- Export to ClickHouse

### Metrics (Prometheus)
- Request rate, latency, errors
- Per-agent cost tracking
- Resource utilization

### Logs (Structured JSON)
- Request/response logging
- Error details with context
- Security events

## Scalability

### Horizontal Scaling
- All services stateless (except databases)
- Kubernetes HPA based on CPU/memory
- Redis for distributed state

### Performance Targets
- Gateway: <50ms p99, 10K RPS/node
- Identity: <100ms p99, 5K RPS/node
- Memory: <200ms p99 (with vector search)
- Policy: <5ms p99, 20K RPS/node

### Database Scaling
- PostgreSQL: Read replicas
- Qdrant: Sharding by agent_did
- Redis: Sentinel for HA

## Deployment Architecture

### Kubernetes Resources
- Deployments: Service pods
- Services: Internal networking
- Ingress: External access
- HPA: Auto-scaling
- ConfigMaps: Configuration
- Secrets: Credentials

### Infrastructure Dependencies
- PostgreSQL 16 (ACID storage)
- Redis 7 (distributed cache)
- Qdrant 1.7+ (vector search)
- ClickHouse (observability)

## Design Principles

1. **Fail Fast**: Validate at boundaries
2. **Explicit Errors**: Rich error context
3. **No Silent Failures**: Log and trace all errors
4. **Bounded Resources**: Timeouts and limits everywhere
5. **Testable Code**: Dependency injection, no global state
6. **Production-Ready**: No TODOs, no placeholders

## Future Enhancements

### Phase 2 (Weeks 11-16)
- ML-based fraud detection
- Multi-modal memory
- Additional protocol adapters

### Phase 3 (Weeks 17-24)
- Multi-tenancy isolation
- Advanced analytics
- Compliance tools (GDPR, SOC 2)
