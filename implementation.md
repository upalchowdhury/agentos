# Agent Economy OS - MVP Implementation Guide

## Executive Summary

**Timeline:** 10 weeks to production-ready MVP  
**Target:** Protocol-agnostic agent infrastructure serving 100+ agents at launch  
**Strategy:** Ship core inference fabric + identity + basic observability first, layer memory + advanced features after validation

---

## MVP Scope (Weeks 1-10)

### Phase 1: Core Infrastructure (Weeks 1-4)
- Cross-Agent Inference Fabric with protocol adapters (A2A, MCP)
- Basic policy engine (rate limits, auth checks)
- Zero-trust identity foundation (DID registry, credential issuance)
- Request routing and load balancing

### Phase 2: Observability + Memory (Weeks 5-7)
- OpenTelemetry integration
- Cost tracking per agent/request
- Basic memory storage (vector + relational)
- Context isolation between agents

### Phase 3: Production Hardening (Weeks 8-10)
- Fraud detection heuristics
- Circuit breakers and fallbacks
- Multi-region deployment
- Dashboard and alerting

---

## Tech Stack

### Core Services (Polyglot by Design)
- **Gateway/Router:** Go (high throughput, <5ms p99)
- **Policy Engine:** Rust (deterministic, fast evaluation)
- **Identity Service:** TypeScript (ecosystem compatibility)
- **Memory Service:** Python (ML/vector integration)
- **Observability:** OpenTelemetry Collector + ClickHouse

### Storage
- **Identity/Credentials:** PostgreSQL 16 (ACID guarantees)
- **Memory Vectors:** Qdrant (native filtering, production-ready)
- **Telemetry:** ClickHouse (columnar, cost-efficient)
- **Cache:** Redis 7.x (session state, rate limits)

### Infrastructure
- **Container Orchestration:** Kubernetes (EKS/GKE)
- **Service Mesh:** Istio (mTLS, observability)
- **Message Queue:** NATS JetStream (low-latency pub/sub)
- **API Gateway:** Kong (external traffic)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     External Clients                         │
│              (Agents, SDKs, HTTP/gRPC/WebSocket)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │   Kong   │ ← External API Gateway
                    │ Gateway  │
                    └────┬─────┘
                         │
        ┌────────────────▼──────────────────┐
        │    Inference Fabric (Go)          │
        │  - Protocol Adapters (A2A/MCP)    │
        │  - Request Router                 │
        │  - Policy Enforcement             │
        └───┬────────────┬─────────────┬────┘
            │            │             │
    ┌───────▼─┐    ┌────▼─────┐  ┌───▼─────────┐
    │Identity │    │  Memory  │  │Observability│
    │ Service │    │  Service │  │   Service   │
    │  (TS)   │    │  (Python)│  │   (OTel)    │
    └───┬─────┘    └────┬─────┘  └───┬─────────┘
        │               │             │
    ┌───▼────┐    ┌────▼─────┐  ┌───▼──────┐
    │Postgres│    │  Qdrant  │  │ClickHouse│
    │  +DID  │    │ +Redis   │  │  +Redis  │
    └────────┘    └──────────┘  └──────────┘
```

---

## Project Structure

```
agent-economy-os/
├── services/
│   ├── gateway/              # Go - Inference Fabric
│   │   ├── cmd/
│   │   │   └── server/
│   │   │       └── main.go
│   │   ├── internal/
│   │   │   ├── adapters/     # Protocol adapters
│   │   │   │   ├── a2a/
│   │   │   │   ├── mcp/
│   │   │   │   └── rest/
│   │   │   ├── router/       # Intelligent routing
│   │   │   ├── policy/       # Policy enforcement client
│   │   │   └── middleware/   # Auth, logging, metrics
│   │   ├── pkg/
│   │   │   └── types/
│   │   ├── go.mod
│   │   └── Dockerfile
│   │
│   ├── policy-engine/        # Rust - Policy Evaluation
│   │   ├── src/
│   │   │   ├── main.rs
│   │   │   ├── engine.rs     # OPA-like evaluation
│   │   │   ├── rules/
│   │   │   └── cache.rs
│   │   ├── Cargo.toml
│   │   └── Dockerfile
│   │
│   ├── identity/             # TypeScript - DID/VC Management
│   │   ├── src/
│   │   │   ├── server.ts
│   │   │   ├── did/
│   │   │   │   ├── registry.ts
│   │   │   │   └── resolver.ts
│   │   │   ├── credentials/
│   │   │   │   ├── issuer.ts
│   │   │   │   └── verifier.ts
│   │   │   └── api/
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   ├── memory/               # Python - Federated Memory
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── vector_store.py
│   │   │   ├── context_manager.py
│   │   │   ├── isolation.py  # Tenant isolation
│   │   │   └── api/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── observability/        # OpenTelemetry Collector Config
│       ├── collector-config.yaml
│       └── dashboards/
│
├── libraries/
│   ├── sdk-typescript/       # Client SDK
│   ├── sdk-python/
│   └── sdk-go/
│
├── infra/
│   ├── terraform/
│   │   ├── aws/
│   │   ├── gcp/
│   │   └── modules/
│   ├── helm/
│   │   ├── gateway/
│   │   ├── identity/
│   │   └── memory/
│   └── k8s/
│       ├── base/
│       └── overlays/
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── runbooks/
│
└── scripts/
    ├── dev-setup.sh
    └── deploy.sh
```

---

## Core Implementation

### 1. Gateway Service (Go)

**`services/gateway/cmd/server/main.go`**
```go
package main

import (
    "context"
    "fmt"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/agent-economy-os/gateway/internal/adapters/a2a"
    "github.com/agent-economy-os/gateway/internal/adapters/mcp"
    "github.com/agent-economy-os/gateway/internal/middleware"
    "github.com/agent-economy-os/gateway/internal/router"
    "github.com/gorilla/mux"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func main() {
    // Initialize tracing
    ctx := context.Background()
    exporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint(os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        log.Fatal(err)
    }
    
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(newResource()),
    )
    otel.SetTracerProvider(tp)

    // Initialize router with adapters
    r := mux.NewRouter()
    
    agentRouter := router.NewRouter(&router.Config{
        IdentityServiceURL: os.Getenv("IDENTITY_SERVICE_URL"),
        PolicyServiceURL:   os.Getenv("POLICY_SERVICE_URL"),
        MemoryServiceURL:   os.Getenv("MEMORY_SERVICE_URL"),
    })

    // Register protocol adapters
    a2aAdapter := a2a.NewAdapter(agentRouter)
    mcpAdapter := mcp.NewAdapter(agentRouter)

    // Middleware chain
    r.Use(middleware.RequestID)
    r.Use(middleware.Authentication(os.Getenv("IDENTITY_SERVICE_URL")))
    r.Use(middleware.Tracing)
    r.Use(middleware.RateLimit)
    r.Use(middleware.Recovery)

    // Routes
    r.HandleFunc("/a2a/v1/invoke", a2aAdapter.HandleInvoke).Methods("POST")
    r.HandleFunc("/mcp/v1/call", mcpAdapter.HandleCall).Methods("POST")
    r.HandleFunc("/health", healthHandler).Methods("GET")
    r.HandleFunc("/metrics", metricsHandler).Methods("GET")

    // Server
    srv := &http.Server{
        Addr:         ":8080",
        Handler:      r,
        ReadTimeout:  30 * time.Second,
        WriteTimeout: 30 * time.Second,
        IdleTimeout:  120 * time.Second,
    }

    // Graceful shutdown
    go func() {
        log.Printf("Gateway listening on %s", srv.Addr)
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    log.Println("Shutting down server...")
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "OK")
}

func metricsHandler(w http.ResponseWriter, r *http.Request) {
    // Prometheus metrics endpoint
    // Implementation here
}
```

**`services/gateway/internal/router/router.go`**
```go
package router

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"

    "github.com/agent-economy-os/gateway/pkg/types"
    "go.opentelemetry.io/otel/trace"
)

type Router struct {
    config            *Config
    identityClient    *IdentityClient
    policyClient      *PolicyClient
    memoryClient      *MemoryClient
    tracer            trace.Tracer
}

type Config struct {
    IdentityServiceURL string
    PolicyServiceURL   string
    MemoryServiceURL   string
}

func NewRouter(config *Config) *Router {
    return &Router{
        config:         config,
        identityClient: NewIdentityClient(config.IdentityServiceURL),
        policyClient:   NewPolicyClient(config.PolicyServiceURL),
        memoryClient:   NewMemoryClient(config.MemoryServiceURL),
    }
}

// RouteRequest handles intelligent routing with policy enforcement
func (r *Router) RouteRequest(ctx context.Context, req *types.AgentRequest) (*types.AgentResponse, error) {
    span := trace.SpanFromContext(ctx)
    span.SetAttributes(
        attribute.String("agent.caller", req.CallerDID),
        attribute.String("agent.target", req.TargetDID),
    )

    // 1. Verify caller identity
    verified, err := r.identityClient.VerifyCredential(ctx, req.CallerDID, req.Credential)
    if err != nil || !verified {
        return nil, fmt.Errorf("identity verification failed: %w", err)
    }

    // 2. Check policy
    allowed, err := r.policyClient.Evaluate(ctx, &PolicyRequest{
        CallerDID: req.CallerDID,
        TargetDID: req.TargetDID,
        Action:    req.Action,
        Context:   req.Context,
    })
    if err != nil || !allowed {
        return nil, fmt.Errorf("policy denied: %w", err)
    }

    // 3. Load relevant memory/context
    memory, err := r.memoryClient.GetContext(ctx, req.TargetDID, req.ConversationID)
    if err != nil {
        // Non-fatal, continue without memory
        span.RecordError(err)
    }

    // 4. Execute request (route to actual agent backend)
    resp, err := r.executeAgent(ctx, req, memory)
    if err != nil {
        return nil, fmt.Errorf("agent execution failed: %w", err)
    }

    // 5. Store interaction in memory
    go r.memoryClient.StoreInteraction(context.Background(), &types.Interaction{
        CallerDID:      req.CallerDID,
        TargetDID:      req.TargetDID,
        ConversationID: req.ConversationID,
        Request:        req,
        Response:       resp,
        Timestamp:      time.Now(),
    })

    return resp, nil
}

func (r *Router) executeAgent(ctx context.Context, req *types.AgentRequest, memory *types.Memory) (*types.AgentResponse, error) {
    // Implementation varies by protocol
    // This would route to actual agent backends
    return &types.AgentResponse{
        Success: true,
        Data:    map[string]interface{}{},
    }, nil
}
```

**`services/gateway/internal/middleware/auth.go`**
```go
package middleware

import (
    "context"
    "net/http"
    "strings"
)

func Authentication(identityServiceURL string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            if authHeader == "" {
                http.Error(w, "Missing authorization", http.StatusUnauthorized)
                return
            }

            // Extract token
            token := strings.TrimPrefix(authHeader, "Bearer ")
            
            // Verify with identity service
            did, err := verifyToken(identityServiceURL, token)
            if err != nil {
                http.Error(w, "Invalid token", http.StatusUnauthorized)
                return
            }

            // Add DID to context
            ctx := context.WithValue(r.Context(), "caller_did", did)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

func verifyToken(serviceURL, token string) (string, error) {
    // Call identity service to verify token
    // Return DID if valid
    return "did:example:123", nil
}
```

---

### 2. Identity Service (TypeScript)

**`services/identity/src/server.ts`**
```typescript
import express from 'express';
import { DIDRegistry } from './did/registry';
import { CredentialIssuer } from './credentials/issuer';
import { CredentialVerifier } from './credentials/verifier';
import { Pool } from 'pg';
import { trace, context } from '@opentelemetry/api';

const app = express();
app.use(express.json());

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
});

// Initialize services
const didRegistry = new DIDRegistry(pool);
const credentialIssuer = new CredentialIssuer(pool);
const credentialVerifier = new CredentialVerifier(pool);

// Routes
app.post('/api/v1/dids', async (req, res) => {
  const tracer = trace.getTracer('identity-service');
  const span = tracer.startSpan('create-did');
  
  try {
    const { agentType, metadata } = req.body;
    const did = await didRegistry.create(agentType, metadata);
    
    span.setAttributes({
      'did.id': did.id,
      'did.type': agentType,
    });
    
    res.json({ did });
  } catch (error) {
    span.recordException(error);
    res.status(500).json({ error: error.message });
  } finally {
    span.end();
  }
});

app.post('/api/v1/credentials/issue', async (req, res) => {
  try {
    const { subjectDID, claims, expiresIn } = req.body;
    const credential = await credentialIssuer.issue(subjectDID, claims, expiresIn);
    res.json({ credential });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/v1/credentials/verify', async (req, res) => {
  try {
    const { credential } = req.body;
    const result = await credentialVerifier.verify(credential);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/api/v1/dids/:did', async (req, res) => {
  try {
    const { did } = req.params;
    const document = await didRegistry.resolve(did);
    res.json({ document });
  } catch (error) {
    res.status(404).json({ error: 'DID not found' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Identity service listening on port ${PORT}`);
});
```

**`services/identity/src/did/registry.ts`**
```typescript
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';
import { DIDDocument } from '../types';

export class DIDRegistry {
  constructor(private pool: Pool) {}

  async create(agentType: string, metadata: any): Promise<DIDDocument> {
    const id = `did:agent:${uuidv4()}`;
    const publicKey = await this.generateKeyPair();
    
    const document: DIDDocument = {
      '@context': ['https://www.w3.org/ns/did/v1'],
      id,
      controller: id,
      verificationMethod: [{
        id: `${id}#key-1`,
        type: 'Ed25519VerificationKey2020',
        controller: id,
        publicKeyMultibase: publicKey,
      }],
      authentication: [`${id}#key-1`],
      assertionMethod: [`${id}#key-1`],
      metadata: {
        agentType,
        ...metadata,
        created: new Date().toISOString(),
      },
    };

    await this.pool.query(
      `INSERT INTO dids (id, document, created_at) VALUES ($1, $2, NOW())`,
      [id, JSON.stringify(document)]
    );

    return document;
  }

  async resolve(did: string): Promise<DIDDocument> {
    const result = await this.pool.query(
      'SELECT document FROM dids WHERE id = $1',
      [did]
    );
    
    if (result.rows.length === 0) {
      throw new Error('DID not found');
    }
    
    return result.rows[0].document;
  }

  private async generateKeyPair(): Promise<string> {
    // Generate Ed25519 key pair
    // Return multibase-encoded public key
    return 'z6Mk...'; // Placeholder
  }
}
```

**`services/identity/src/credentials/issuer.ts`**
```typescript
import { Pool } from 'pg';
import * as jose from 'jose';

export class CredentialIssuer {
  constructor(private pool: Pool) {}

  async issue(subjectDID: string, claims: any, expiresIn: string = '30d'): Promise<string> {
    const now = Math.floor(Date.now() / 1000);
    const exp = now + this.parseExpiry(expiresIn);

    const payload = {
      iss: 'did:agent:issuer', // Platform issuer DID
      sub: subjectDID,
      iat: now,
      exp,
      vc: {
        '@context': ['https://www.w3.org/2018/credentials/v1'],
        type: ['VerifiableCredential', 'AgentCredential'],
        credentialSubject: {
          id: subjectDID,
          ...claims,
        },
      },
    };

    // Sign with platform private key
    const privateKey = await this.getIssuerPrivateKey();
    const jwt = await new jose.SignJWT(payload)
      .setProtectedHeader({ alg: 'EdDSA' })
      .sign(privateKey);

    // Store credential record
    await this.pool.query(
      `INSERT INTO credentials (id, subject_did, jwt, issued_at, expires_at) 
       VALUES (gen_random_uuid(), $1, $2, to_timestamp($3), to_timestamp($4))`,
      [subjectDID, jwt, now, exp]
    );

    return jwt;
  }

  private parseExpiry(expiresIn: string): number {
    const match = expiresIn.match(/^(\d+)([dhm])$/);
    if (!match) throw new Error('Invalid expiry format');
    
    const value = parseInt(match[1]);
    const unit = match[2];
    
    switch (unit) {
      case 'd': return value * 86400;
      case 'h': return value * 3600;
      case 'm': return value * 60;
      default: throw new Error('Invalid time unit');
    }
  }

  private async getIssuerPrivateKey(): Promise<jose.KeyLike> {
    // Load platform's private key from secure storage
    // For MVP, can use environment variable
    const jwk = JSON.parse(process.env.ISSUER_PRIVATE_KEY);
    return jose.importJWK(jwk);
  }
}
```

---

### 3. Memory Service (Python)

**`services/memory/src/main.py`**
```python
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from typing import List, Optional
import asyncpg
import os

from .vector_store import VectorStore
from .context_manager import ContextManager
from .isolation import TenantIsolation

# Database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(
        os.getenv("DATABASE_URL"),
        min_size=10,
        max_size=20
    )
    yield
    await db_pool.close()

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

# Initialize services
qdrant = QdrantClient(url=os.getenv("QDRANT_URL"))
vector_store = VectorStore(qdrant)
context_manager = ContextManager(db_pool, vector_store)
tenant_isolation = TenantIsolation(db_pool)

@app.post("/api/v1/memories")
async def store_memory(
    agent_did: str,
    conversation_id: str,
    content: str,
    metadata: dict = {}
):
    """Store a memory with vector embedding"""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("store_memory") as span:
        span.set_attributes({
            "agent.did": agent_did,
            "conversation.id": conversation_id,
        })
        
        try:
            # Check tenant isolation
            if not await tenant_isolation.can_write(agent_did, conversation_id):
                raise HTTPException(403, "Access denied")
            
            memory_id = await context_manager.store(
                agent_did=agent_did,
                conversation_id=conversation_id,
                content=content,
                metadata=metadata
            )
            
            return {"memory_id": memory_id}
        except Exception as e:
            span.record_exception(e)
            raise HTTPException(500, str(e))

@app.get("/api/v1/memories/search")
async def search_memories(
    agent_did: str,
    conversation_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 10
):
    """Search memories with vector similarity"""
    try:
        # Check read access
        if not await tenant_isolation.can_read(agent_did, conversation_id):
            raise HTTPException(403, "Access denied")
        
        results = await context_manager.search(
            agent_did=agent_did,
            conversation_id=conversation_id,
            query=query,
            limit=limit
        )
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/v1/context/{conversation_id}")
async def get_context(
    conversation_id: str,
    agent_did: str,
    limit: int = 50
):
    """Get recent context for a conversation"""
    try:
        if not await tenant_isolation.can_read(agent_did, conversation_id):
            raise HTTPException(403, "Access denied")
        
        context = await context_manager.get_recent_context(
            conversation_id=conversation_id,
            limit=limit
        )
        
        return {"context": context}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/v1/interactions")
async def store_interaction(
    caller_did: str,
    target_did: str,
    conversation_id: str,
    request: dict,
    response: dict
):
    """Store agent interaction for audit/replay"""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO interactions 
            (caller_did, target_did, conversation_id, request, response, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            """,
            caller_did, target_did, conversation_id,
            json.dumps(request), json.dumps(response)
        )
    
    return {"status": "stored"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**`services/memory/src/vector_store.py`**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict

class VectorStore:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "agent_memories"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=Distance.COSINE
                )
            )
    
    async def store(
        self,
        memory_id: str,
        content: str,
        agent_did: str,
        conversation_id: str,
        metadata: Dict = {}
    ):
        """Store memory with vector embedding"""
        embedding = self.model.encode(content).tolist()
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "memory_id": memory_id,
                "content": content,
                "agent_did": agent_did,
                "conversation_id": conversation_id,
                **metadata
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    async def search(
        self,
        query: str,
        agent_did: str,
        conversation_id: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search memories by semantic similarity"""
        query_vector = self.model.encode(query).tolist()
        
        # Build filter
        must_conditions = [
            FieldCondition(
                key="agent_did",
                match=MatchValue(value=agent_did)
            )
        ]
        
        if conversation_id:
            must_conditions.append(
                FieldCondition(
                    key="conversation_id",
                    match=MatchValue(value=conversation_id)
                )
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=must_conditions),
            limit=limit
        )
        
        return [
            {
                "memory_id": hit.payload["memory_id"],
                "content": hit.payload["content"],
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() 
                            if k not in ["memory_id", "content", "agent_did", "conversation_id"]}
            }
            for hit in results
        ]
```

---

### 4. Policy Engine (Rust)

**`services/policy-engine/src/main.rs`**
```rust
use actix_web::{web, App, HttpResponse, HttpServer};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use redis::aio::ConnectionManager;

mod engine;
mod rules;
mod cache;

use engine::PolicyEngine;
use rules::Rule;

#[derive(Debug, Deserialize)]
struct PolicyRequest {
    caller_did: String,
    target_did: String,
    action: String,
    context: serde_json::Value,
}

#[derive(Debug, Serialize)]
struct PolicyResponse {
    allowed: bool,
    reason: Option<String>,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();
    
    // Initialize Redis cache
    let redis_client = redis::Client::open(
        std::env::var("REDIS_URL").expect("REDIS_URL must be set")
    ).expect("Failed to connect to Redis");
    let redis_conn = ConnectionManager::new(redis_client).await.unwrap();
    
    // Initialize policy engine
    let engine = Arc::new(RwLock::new(PolicyEngine::new(redis_conn)));
    
    // Load default rules
    load_default_rules(&engine).await;
    
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(engine.clone()))
            .route("/api/v1/evaluate", web::post().to(evaluate))
            .route("/api/v1/rules", web::post().to(add_rule))
            .route("/health", web::get().to(health))
    })
    .bind(("0.0.0.0", 8080))?
    .run()
    .await
}

async fn evaluate(
    req: web::Json<PolicyRequest>,
    engine: web::Data<Arc<RwLock<PolicyEngine>>>,
) -> HttpResponse {
    let engine = engine.read().await;
    
    match engine.evaluate(&req.caller_did, &req.target_did, &req.action, &req.context).await {
        Ok(allowed) => {
            HttpResponse::Ok().json(PolicyResponse {
                allowed,
                reason: if allowed { None } else { Some("Policy denied".into()) },
            })
        }
        Err(e) => {
            HttpResponse::InternalServerError().json(PolicyResponse {
                allowed: false,
                reason: Some(format!("Evaluation error: {}", e)),
            })
        }
    }
}

async fn add_rule(
    rule: web::Json<Rule>,
    engine: web::Data<Arc<RwLock<PolicyEngine>>>,
) -> HttpResponse {
    let mut engine = engine.write().await;
    engine.add_rule(rule.into_inner());
    HttpResponse::Ok().json(serde_json::json!({"status": "rule added"}))
}

async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status": "healthy"}))
}

async fn load_default_rules(engine: &Arc<RwLock<PolicyEngine>>) {
    let mut engine = engine.write().await;
    
    // Rate limit rule: max 100 requests per minute per agent
    engine.add_rule(Rule::RateLimit {
        max_requests: 100,
        window_seconds: 60,
    });
    
    // Cost limit rule: max $10 per hour per agent
    engine.add_rule(Rule::CostLimit {
        max_cost_cents: 1000,
        window_seconds: 3600,
    });
}
```

**`services/policy-engine/src/engine.rs`**
```rust
use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use crate::rules::Rule;
use serde_json::Value;

pub struct PolicyEngine {
    rules: Vec<Rule>,
    redis: ConnectionManager,
}

impl PolicyEngine {
    pub fn new(redis: ConnectionManager) -> Self {
        Self {
            rules: Vec::new(),
            redis,
        }
    }
    
    pub fn add_rule(&mut self, rule: Rule) {
        self.rules.push(rule);
    }
    
    pub async fn evaluate(
        &self,
        caller_did: &str,
        target_did: &str,
        action: &str,
        context: &Value,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        // Evaluate all rules
        for rule in &self.rules {
            if !self.evaluate_rule(rule, caller_did, target_did, action, context).await? {
                return Ok(false);
            }
        }
        
        Ok(true)
    }
    
    async fn evaluate_rule(
        &self,
        rule: &Rule,
        caller_did: &str,
        _target_did: &str,
        _action: &str,
        _context: &Value,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        match rule {
            Rule::RateLimit { max_requests, window_seconds } => {
                self.check_rate_limit(caller_did, *max_requests, *window_seconds).await
            }
            Rule::CostLimit { max_cost_cents, window_seconds } => {
                self.check_cost_limit(caller_did, *max_cost_cents, *window_seconds).await
            }
        }
    }
    
    async fn check_rate_limit(
        &self,
        caller_did: &str,
        max_requests: u32,
        window_seconds: u64,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        let key = format!("rate_limit:{}:{}", caller_did, window_seconds);
        let mut conn = self.redis.clone();
        
        let count: u32 = conn.incr(&key, 1).await?;
        if count == 1 {
            conn.expire(&key, window_seconds as usize).await?;
        }
        
        Ok(count <= max_requests)
    }
    
    async fn check_cost_limit(
        &self,
        caller_did: &str,
        max_cost_cents: u64,
        window_seconds: u64,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        let key = format!("cost_limit:{}:{}", caller_did, window_seconds);
        let mut conn = self.redis.clone();
        
        let cost: u64 = conn.get(&key).await.unwrap_or(0);
        Ok(cost < max_cost_cents)
    }
}
```

---

## Database Schemas

**`infra/migrations/001_initial_schema.sql`**
```sql
-- DIDs table
CREATE TABLE dids (
    id VARCHAR(255) PRIMARY KEY,
    document JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dids_created ON dids(created_at);

-- Credentials table
CREATE TABLE credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_did VARCHAR(255) NOT NULL,
    jwt TEXT NOT NULL,
    issued_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_credentials_subject ON credentials(subject_did);
CREATE INDEX idx_credentials_expires ON credentials(expires_at);

-- Interactions table (audit log)
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caller_did VARCHAR(255) NOT NULL,
    target_did VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interactions_caller ON interactions(caller_did, created_at);
CREATE INDEX idx_interactions_conversation ON interactions(conversation_id, created_at);

-- Memories table
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_memories_agent ON memories(agent_did, created_at);
CREATE INDEX idx_memories_conversation ON memories(conversation_id, created_at);

-- Tenant access control
CREATE TABLE tenant_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    resource_type VARCHAR(50) NOT NULL, -- 'conversation', 'memory', etc.
    resource_id VARCHAR(255) NOT NULL,
    permission VARCHAR(50) NOT NULL, -- 'read', 'write', 'admin'
    granted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_tenant_access_unique ON tenant_access(agent_did, resource_type, resource_id, permission);

-- Cost tracking
CREATE TABLE cost_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'inference', 'memory_read', 'memory_write'
    cost_cents INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cost_events_agent ON cost_events(agent_did, created_at);
```

---

## Kubernetes Deployment

**`infra/helm/gateway/values.yaml`**
```yaml
replicaCount: 3

image:
  repository: agent-economy-os/gateway
  tag: "0.1.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.agentos.io
      paths:
        - path: /
          pathType: Prefix

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

env:
  - name: IDENTITY_SERVICE_URL
    value: "http://identity-service:3000"
  - name: POLICY_SERVICE_URL
    value: "http://policy-engine:8080"
  - name: MEMORY_SERVICE_URL
    value: "http://memory-service:8000"
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "otel-collector:4317"

serviceMonitor:
  enabled: true
  interval: 30s
```

**`infra/helm/gateway/templates/deployment.yaml`**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "gateway.fullname" . }}
  labels:
    {{- include "gateway.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "gateway.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
      labels:
        {{- include "gateway.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: gateway
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        env:
          {{- toYaml .Values.env | nindent 12 }}
```

---

## OpenTelemetry Collector Configuration

**`services/observability/collector-config.yaml`**
```yaml
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
  
  attributes:
    actions:
      - key: service.namespace
        value: agent-economy-os
        action: insert
  
  resource:
    attributes:
      - key: deployment.environment
        value: ${ENVIRONMENT}
        action: insert

exporters:
  clickhouse:
    endpoint: tcp://clickhouse:9000
    database: observability
    traces_table_name: otel_traces
    logs_table_name: otel_logs
    metrics_table_name: otel_metrics
    ttl_days: 30
    timeout: 5s
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
  
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: agentos
    
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, attributes, resource]
      exporters: [clickhouse]
    
    metrics:
      receivers: [otlp]
      processors: [batch, attributes, resource]
      exporters: [clickhouse, prometheus]
    
    logs:
      receivers: [otlp]
      processors: [batch, attributes, resource]
      exporters: [clickhouse]
```

---

## Production Expansion Path

### Week 11-16: Scale & Sophistication
1. **Advanced Policy Engine**
   - ML-based fraud detection (train on interaction patterns)
   - Dynamic reputation scoring
   - Anomaly detection for unauthorized agent behavior

2. **Memory Enhancements**
   - Multi-modal memory (images, audio embeddings)
   - Cross-agent memory sharing with fine-grained permissions
   - Memory compression and archival strategies

3. **Protocol Expansion**
   - Add OpenAI's Swarm protocol adapter
   - LangGraph integration
   - Custom enterprise protocol support

### Week 17-24: Enterprise Features
1. **Multi-tenancy**
   - Namespace isolation
   - Per-tenant billing
   - Custom policy templates

2. **Advanced Observability**
   - Agent behavior analytics dashboard
   - Cost optimization recommendations
   - Predictive scaling

3. **Compliance & Audit**
   - Immutable audit logs
   - GDPR/CCPA compliance tools
   - SOC 2 readiness

---

## Development Workflow

### Local Development Setup

**`scripts/dev-setup.sh`**
```bash
#!/bin/bash
set -e

echo "Setting up Agent Economy OS development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl required"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "Helm required"; exit 1; }

# Start local Kubernetes cluster
kind create cluster --name agentos-dev --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
  - containerPort: 443
    hostPort: 8443
EOF

# Install infrastructure
kubectl create namespace agentos

# PostgreSQL
helm install postgres bitnami/postgresql \
  --namespace agentos \
  --set auth.database=agentos \
  --set primary.persistence.size=10Gi

# Redis
helm install redis bitnami/redis \
  --namespace agentos \
  --set architecture=standalone

# Qdrant
helm install qdrant qdrant/qdrant \
  --namespace agentos

# ClickHouse
helm install clickhouse bitnami/clickhouse \
  --namespace agentos

# Build and deploy services
docker-compose -f docker-compose.dev.yaml build
kind load docker-image agent-economy-os/gateway:dev --name agentos-dev
kind load docker-image agent-economy-os/identity:dev --name agentos-dev
kind load docker-image agent-economy-os/memory:dev --name agentos-dev
kind load docker-image agent-economy-os/policy-engine:dev --name agentos-dev

# Deploy services
helm install gateway ./infra/helm/gateway --namespace agentos
helm install identity ./infra/helm/identity --namespace agentos
helm install memory ./infra/helm/memory --namespace agentos
helm install policy-engine ./infra/helm/policy-engine --namespace agentos

echo "Development environment ready!"
echo "Access gateway at: http://localhost:8080"
```

### Testing Strategy

**`services/gateway/internal/router/router_test.go`**
```go
package router

import (
    "context"
    "testing"
    "time"

    "github.com/agent-economy-os/gateway/pkg/types"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

func TestRouteRequest_Success(t *testing.T) {
    // Mock dependencies
    identityClient := new(MockIdentityClient)
    policyClient := new(MockPolicyClient)
    memoryClient := new(MockMemoryClient)

    router := &Router{
        identityClient: identityClient,
        policyClient:   policyClient,
        memoryClient:   memoryClient,
    }

    // Setup mocks
    identityClient.On("VerifyCredential", mock.Anything, "did:agent:caller", "credential").Return(true, nil)
    policyClient.On("Evaluate", mock.Anything, mock.Anything).Return(true, nil)
    memoryClient.On("GetContext", mock.Anything, "did:agent:target", "conv-123").Return(&types.Memory{}, nil)

    // Execute
    req := &types.AgentRequest{
        CallerDID:      "did:agent:caller",
        TargetDID:      "did:agent:target",
        ConversationID: "conv-123",
        Action:         "query",
        Credential:     "credential",
    }

    resp, err := router.RouteRequest(context.Background(), req)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, resp)
    identityClient.AssertExpectations(t)
    policyClient.AssertExpectations(t)
}

func TestRouteRequest_PolicyDenied(t *testing.T) {
    // Similar structure - test policy denial
}

func TestRouteRequest_RateLimit(t *testing.T) {
    // Test rate limiting behavior
}
```

---

## Monitoring & Alerting

**`infra/helm/observability/dashboards/gateway-dashboard.json`**
```json
{
  "dashboard": {
    "title": "Agent Economy OS - Gateway",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(agentos_gateway_requests_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      },
      {
        "title": "P99 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(agentos_gateway_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{method}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(agentos_gateway_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Agent Costs (per hour)",
        "targets": [
          {
            "expr": "sum by(agent_did) (rate(agentos_cost_cents_total[1h]))",
            "legendFormat": "{{agent_did}}"
          }
        ]
      }
    ]
  }
}
```

---

## SDK Example (TypeScript)

**`libraries/sdk-typescript/src/client.ts`**
```typescript
import axios, { AxiosInstance } from 'axios';

export interface AgentOSConfig {
  apiUrl: string;
  agentDID: string;
  credential: string;
}

export class AgentOSClient {
  private client: AxiosInstance;
  private agentDID: string;
  private credential: string;

  constructor(config: AgentOSConfig) {
    this.agentDID = config.agentDID;
    this.credential = config.credential;
    
    this.client = axios.create({
      baseURL: config.apiUrl,
      timeout: 30000,
      headers: {
        'Authorization': `Bearer ${config.credential}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async invokeAgent(targetDID: string, action: string, params: any, conversationID?: string): Promise<any> {
    const response = await this.client.post('/a2a/v1/invoke', {
      caller_did: this.agentDID,
      target_did: targetDID,
      action,
      params,
      conversation_id: conversationID || this.generateConversationID(),
      credential: this.credential,
    });

    return response.data;
  }

  async storeMemory(content: string, conversationID: string, metadata: any = {}): Promise<string> {
    const response = await this.client.post('/api/v1/memories', {
      agent_did: this.agentDID,
      conversation_id: conversationID,
      content,
      metadata,
    });

    return response.data.memory_id;
  }

  async searchMemories(query: string, conversationID?: string, limit: number = 10): Promise<any[]> {
    const response = await this.client.get('/api/v1/memories/search', {
      params: {
        agent_did: this.agentDID,
        conversation_id: conversationID,
        query,
        limit,
      },
    });

    return response.data.results;
  }

  private generateConversationID(): string {
    return `${this.agentDID}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  }
}

// Usage example
const client = new AgentOSClient({
  apiUrl: 'https://api.agentos.io',
  agentDID: 'did:agent:my-agent-123',
  credential: 'eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...',
});

await client.invokeAgent(
  'did:agent:task-executor',
  'execute',
  { task: 'analyze_data', dataset: 'users.csv' },
  'conv-abc-123'
);
```

---

## CI/CD Pipeline

**`.github/workflows/deploy.yaml`**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Gateway Tests
        working-directory: services/gateway
        run: |
          go test -v -cover ./...
      
      - name: Run Identity Tests
        working-directory: services/identity
        run: |
          npm test
      
      - name: Run Memory Tests
        working-directory: services/memory
        run: |
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [gateway, identity, memory, policy-engine]
    steps:
      - uses: actions/checkout@v3
      
      - name: Build ${{ matrix.service }}
        run: |
          docker build -t ${{ secrets.REGISTRY }}/${{ matrix.service }}:${{ github.sha }} \
            services/${{ matrix.service }}
      
      - name: Push to Registry
        run: |
          docker push ${{ secrets.REGISTRY }}/${{ matrix.service }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to EKS
        run: |
          helm upgrade --install gateway ./infra/helm/gateway \
            --set image.tag=${{ github.sha }} \
            --namespace production
```

---

## Quick Start Guide

### 1. Clone Repository
```bash
git clone https://github.com/your-org/agent-economy-os.git
cd agent-economy-os
```

### 2. Run Local Development
```bash
./scripts/dev-setup.sh
```

### 3. Register an Agent
```bash
curl -X POST http://localhost:8080/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "task_executor",
    "metadata": {"name": "My First Agent"}
  }'
```

### 4. Issue Credential
```bash
curl -X POST http://localhost:8080/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subject_did": "did:agent:123...",
    "claims": {"capabilities": ["execute", "read"]},
    "expires_in": "30d"
  }'
```

### 5. Make an Agent Call
```bash
curl -X POST http://localhost:8080/a2a/v1/invoke \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_did": "did:agent:caller",
    "target_did": "did:agent:target",
    "action": "execute",
    "params": {"task": "hello_world"}
  }'
```

---

## Key Metrics to Track

### Business Metrics
- **Agents Onboarded:** Track growth rate
- **Requests Per Second:** Total throughput
- **Revenue Per Agent:** Average spend
- **Protocol Mix:** Which protocols dominate

### Technical Metrics
- **P99 Latency:** < 50ms target
- **Availability:** 99.95% SLA
- **Error Rate:** < 0.1%
- **Cost Per Request:** Track infrastructure efficiency

### Security Metrics
- **Fraud Detection Rate:** False positives vs true positives
- **Policy Violations:** Unauthorized action attempts
- **Credential Revocations:** Trust graph health

---

## Next Steps After MVP

1. **Week 11:** Launch beta with 5-10 design partners
2. **Week 12-14:** Integrate feedback, add missing protocol adapters
3. **Week 15-16:** Public launch with SDKs for 5 languages
4. **Week 17-20:** Enterprise features (multi-tenancy, advanced RBAC)
5. **Week 21-24:** ML-powered fraud detection and reputation system

---

## Appendix: Full File Checklist

### Must-Have for MVP Launch
- [ ] Gateway service (Go)
- [ ] Identity service (TypeScript)
- [ ] Memory service (Python)
- [ ] Policy engine (Rust)
- [ ] PostgreSQL migrations
- [ ] Helm charts for all services
- [ ] OpenTelemetry collector config
- [ ] TypeScript SDK
- [ ] Basic documentation
- [ ] Dev setup script

### Nice-to-Have for MVP
- [ ] Python SDK
- [ ] Go SDK
- [ ] Grafana dashboards
- [ ] Load testing scripts
- [ ] Performance benchmarks
- [ ] Security audit




What's Missing

RBAC/ABAC - No role/permission model
Content Guardrails - No PII/toxicity detection
Policy Rules - Only rate/cost limits, no attribute-based policies

Where to Add
1. Enhanced Policy Engine Rules
services/policy-engine/src/rules.rs
rust#[derive(Debug, Deserialize, Serialize)]
pub enum Rule {
    RateLimit { max_requests: u32, window_seconds: u64 },
    CostLimit { max_cost_cents: u64, window_seconds: u64 },
    
    // NEW: RBAC
    RequireRole { roles: Vec<String> },
    RequirePermission { resource: String, action: String },
    
    // NEW: ABAC
    AttributeMatch { 
        attribute: String, 
        operator: Operator, 
        value: String 
    },
    
    // NEW: Content Guardrails
    BlockPII { types: Vec<PIIType> },
    BlockToxicity { threshold: f32 },
    RequireContentCompliance { policies: Vec<String> },
}

#[derive(Debug, Deserialize, Serialize)]
pub enum PIIType {
    SSN, CreditCard, Email, PhoneNumber, IPAddress
}

#[derive(Debug, Deserialize, Serialize)]
pub enum Operator {
    Equals, NotEquals, Contains, GreaterThan, LessThan
}
2. Content Filter Service
services/gateway/internal/filters/content_filter.go
gopackage filters

import (
    "context"
    "regexp"
)

type ContentFilter struct {
    piiDetector     *PIIDetector
    toxicityChecker *ToxicityChecker
}

func (f *ContentFilter) ScanRequest(ctx context.Context, req *types.AgentRequest) error {
    // Check PII
    if pii := f.piiDetector.Detect(req.Params); len(pii) > 0 {
        return &PolicyViolation{
            Type: "pii_detected",
            Details: pii,
        }
    }
    
    // Check toxicity
    if score := f.toxicityChecker.Score(req.Params); score > 0.8 {
        return &PolicyViolation{
            Type: "toxic_content",
            Score: score,
        }
    }
    
    return nil
}

type PIIDetector struct {
    patterns map[string]*regexp.Regexp
}

func NewPIIDetector() *PIIDetector {
    return &PIIDetector{
        patterns: map[string]*regexp.Regexp{
            "ssn":         regexp.MustCompile(`\b\d{3}-\d{2}-\d{4}\b`),
            "credit_card": regexp.MustCompile(`\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b`),
            "email":       regexp.MustCompile(`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`),
            "phone":       regexp.MustCompile(`\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`),
        },
    }
}

func (d *PIIDetector) Detect(data interface{}) []PIIMatch {
    text := stringify(data)
    var matches []PIIMatch
    
    for piiType, pattern := range d.patterns {
        if pattern.MatchString(text) {
            matches = append(matches, PIIMatch{
                Type: piiType,
                Redacted: pattern.ReplaceAllString(text, "[REDACTED]"),
            })
        }
    }
    return matches
}
3. RBAC in Identity Service
services/identity/src/rbac/roles.ts
typescriptexport interface Role {
  name: string;
  permissions: Permission[];
}

export interface Permission {
  resource: string;  // e.g., "agent:invoke", "memory:read"
  action: string;    // e.g., "read", "write", "execute"
  constraints?: Record<string, any>;  // ABAC attributes
}

export class RBACManager {
  async assignRole(agentDID: string, role: string): Promise<void> {
    await this.pool.query(
      'INSERT INTO agent_roles (agent_did, role_name) VALUES ($1, $2)',
      [agentDID, role]
    );
  }

  async checkPermission(
    agentDID: string, 
    resource: string, 
    action: string,
    context: Record<string, any>
  ): Promise<boolean> {
    const roles = await this.getAgentRoles(agentDID);
    
    for (const role of roles) {
      const permissions = await this.getRolePermissions(role);
      
      for (const perm of permissions) {
        if (this.matchesPermission(perm, resource, action, context)) {
          return true;
        }
      }
    }
    
    return false;
  }

  private matchesPermission(
    perm: Permission, 
    resource: string, 
    action: string,
    context: Record<string, any>
  ): boolean {
    if (perm.resource !== resource || perm.action !== action) {
      return false;
    }
    
    // ABAC: Check constraints
    if (perm.constraints) {
      return this.evaluateConstraints(perm.constraints, context);
    }
    
    return true;
  }

  private evaluateConstraints(
    constraints: Record<string, any>,
    context: Record<string, any>
  ): boolean {
    for (const [key, expected] of Object.entries(constraints)) {
      if (context[key] !== expected) {
        return false;
      }
    }
    return true;
  }
}
4. Database Schema Addition
infra/migrations/002_rbac_schema.sql
sql-- Roles
CREATE TABLE roles (
    name VARCHAR(50) PRIMARY KEY,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Permissions
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) REFERENCES roles(name),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    constraints JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Roles (many-to-many)
CREATE TABLE agent_roles (
    agent_did VARCHAR(255) REFERENCES dids(id),
    role_name VARCHAR(50) REFERENCES roles(name),
    granted_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (agent_did, role_name)
);

-- Content Policy Violations
CREATE TABLE content_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_did VARCHAR(255) NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Default roles
INSERT INTO roles (name, description) VALUES
    ('agent:basic', 'Basic agent with read-only access'),
    ('agent:executor', 'Can execute tasks and write memory'),
    ('agent:admin', 'Full administrative access');

-- Default permissions
INSERT INTO permissions (role_name, resource, action) VALUES
    ('agent:basic', 'agent:invoke', 'read'),
    ('agent:basic', 'memory:read', 'read'),
    ('agent:executor', 'agent:invoke', 'execute'),
    ('agent:executor', 'memory:write', 'write'),
    ('agent:admin', '*', '*');
5. Integration in Gateway
services/gateway/internal/router/router.go (updated)
gofunc (r *Router) RouteRequest(ctx context.Context, req *types.AgentRequest) (*types.AgentResponse, error) {
    span := trace.SpanFromContext(ctx)
    
    // 1. Verify identity
    verified, err := r.identityClient.VerifyCredential(ctx, req.CallerDID, req.Credential)
    if err != nil || !verified {
        return nil, fmt.Errorf("identity verification failed: %w", err)
    }
    
    // 2. Check RBAC/ABAC permissions
    hasPermission, err := r.identityClient.CheckPermission(ctx, req.CallerDID, 
        "agent:invoke", "execute", req.Context)
    if err != nil || !hasPermission {
        return nil, fmt.Errorf("permission denied: %w", err)
    }
    
    // 3. Content filtering
    if err := r.contentFilter.ScanRequest(ctx, req); err != nil {
        r.recordViolation(ctx, req.CallerDID, err)
        return nil, fmt.Errorf("content policy violation: %w", err)
    }
    
    // 4. Policy evaluation (rate limits, cost limits)
    allowed, err := r.policyClient.Evaluate(ctx, &PolicyRequest{
        CallerDID: req.CallerDID,
        TargetDID: req.TargetDID,
        Action:    req.Action,
        Context:   req.Context,
    })
    if err != nil || !allowed {
        return nil, fmt.Errorf("policy denied: %w", err)
    }
    
    // Continue with execution...
}
Quick Implementation Priority

RBAC schema + basic role checks
PII detection (regex-based)
 ABAC with context evaluation
 Toxicity detection (integrate Perspective API or local model)

Add to existing codebase - all services already have hooks for this via the policy engine and middleware.RetryClaude can make mistakes. Please double-check responses.




This guide provides everything needed to build a production-ready Agent Economy OS MVP in 10 weeks, with clear paths to scale to enterprise-grade infrastructure.