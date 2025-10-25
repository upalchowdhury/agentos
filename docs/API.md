# API Documentation

## Gateway Service (Port 8080)

### Agent-to-Agent Protocol

#### POST /a2a/v1/invoke

Invoke another agent with a specific action.

**Headers:**
- `Authorization: Bearer <JWT_CREDENTIAL>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "caller_did": "did:agent:caller-id",
  "target_did": "did:agent:target-id",
  "action": "execute",
  "params": {
    "task": "analyze",
    "data": "sample"
  },
  "conversation_id": "conv-123",
  "credential": "jwt-token"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "result": "completed"
  }
}
```

### Model Context Protocol

#### POST /mcp/v1/call

MCP-compatible agent invocation.

Same format as A2A endpoint.

### Health Check

#### GET /health

Returns service health status.

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Identity Service (Port 3000)

### DID Management

#### POST /api/v1/dids

Create a new Decentralized Identifier.

**Request Body:**
```json
{
  "agentType": "assistant",
  "metadata": {
    "name": "Agent Name",
    "description": "Description"
  }
}
```

**Response:**
```json
{
  "did": {
    "id": "did:agent:uuid",
    "@context": ["https://www.w3.org/ns/did/v1"],
    "controller": "did:agent:uuid",
    "verificationMethod": [...],
    "metadata": {...}
  }
}
```

#### GET /api/v1/dids/:did

Resolve a DID document.

**Response:**
```json
{
  "document": {
    "id": "did:agent:uuid",
    ...
  }
}
```

#### GET /api/v1/dids

List all DIDs with pagination.

**Query Parameters:**
- `limit` (default: 100, max: 1000)
- `offset` (default: 0)

### Credentials

#### POST /api/v1/credentials/issue

Issue a Verifiable Credential.

**Request Body:**
```json
{
  "subjectDID": "did:agent:uuid",
  "claims": {
    "capabilities": ["read", "write"],
    "role": "agent"
  },
  "expiresIn": "30d"
}
```

**Response:**
```json
{
  "credential": "eyJhbGc..."
}
```

#### POST /api/v1/credentials/verify

Verify a credential.

**Request Body:**
```json
{
  "credential": "eyJhbGc..."
}
```

**Response:**
```json
{
  "valid": true,
  "did": "did:agent:uuid"
}
```

#### POST /api/v1/credentials/revoke

Revoke a credential.

**Request Body:**
```json
{
  "credential": "eyJhbGc..."
}
```

---

## Memory Service (Port 8000)

### Memory Storage

#### POST /api/v1/memories

Store a memory with vector embedding.

**Request Body:**
```json
{
  "agent_did": "did:agent:uuid",
  "conversation_id": "conv-123",
  "content": "User asked about pricing",
  "metadata": {
    "topic": "pricing"
  }
}
```

**Response:**
```json
{
  "memory_id": "uuid"
}
```

#### GET /api/v1/memories/search

Search memories by semantic similarity.

**Query Parameters:**
- `agent_did` (required)
- `conversation_id` (optional)
- `query` (optional)
- `limit` (default: 10, max: 100)

**Response:**
```json
{
  "results": [
    {
      "memory_id": "uuid",
      "content": "...",
      "score": 0.95,
      "metadata": {...}
    }
  ]
}
```

#### GET /api/v1/context/:conversation_id

Get recent context for a conversation.

**Query Parameters:**
- `agent_did` (required)
- `limit` (default: 50, max: 500)

**Response:**
```json
{
  "context": [
    {
      "memory_id": "uuid",
      "content": "...",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Interaction Logging

#### POST /api/v1/interactions

Store agent interaction for audit.

**Request Body:**
```json
{
  "caller_did": "did:agent:caller",
  "target_did": "did:agent:target",
  "conversation_id": "conv-123",
  "request": {...},
  "response": {...}
}
```

---

## Policy Engine (Port 8081)

### Policy Evaluation

#### POST /api/v1/evaluate

Evaluate a policy request.

**Request Body:**
```json
{
  "caller_did": "did:agent:caller",
  "target_did": "did:agent:target",
  "action": "execute",
  "context": {...}
}
```

**Response:**
```json
{
  "allowed": true,
  "reason": null
}
```

#### POST /api/v1/rules

Add a policy rule.

**Request Body:**
```json
{
  "type": "RateLimit",
  "max_requests": 100,
  "window_seconds": 60
}
```

#### POST /api/v1/cost

Record cost for an agent.

**Request Body:**
```json
{
  "caller_did": "did:agent:uuid",
  "cost_cents": 50,
  "window_seconds": 3600
}
```

---

## Error Responses

All services return errors in this format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid credentials)
- `403` - Forbidden (policy denied)
- `404` - Not Found
- `500` - Internal Server Error
