# Agent Economy OS - Complete Setup Guide

**Last Updated:** October 25, 2025  
**Version:** 0.1.0

This guide walks you through the complete setup process from zero to a fully functional Agent Economy OS deployment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install Dependencies](#install-dependencies)
3. [Start the Platform](#start-the-platform)
4. [Verify Installation](#verify-installation)
5. [Register Your First Agent](#register-your-first-agent)
6. [Test Agent Invocation](#test-agent-invocation)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

Ensure you have the following installed on your system:

| Software | Version | Check Command |
|----------|---------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker-compose --version` |
| Go | 1.21+ | `go version` |
| Node.js | 20+ | `node --version` |
| Python | 3.11+ | `python3 --version` |
| Rust | 1.75+ | `cargo --version` |

### Install Missing Tools

**macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install docker docker-compose go node python@3.11 rust
```

**Linux (Ubuntu/Debian):**
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Go
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz

# Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python
sudo apt-get install -y python3.11 python3-pip

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

---

## Install Dependencies

Navigate to the project root and install dependencies for each service:

```bash
cd /Users/upalc/AgentOS/agentos
```

### 1. Gateway Service (Go)

```bash
cd services/gateway
go mod download
go mod tidy
cd ../..
```

### 2. Identity Service (TypeScript)

```bash
cd services/identity
npm install
cd ../..
```

### 3. Memory Service (Python)

```bash
cd services/memory
pip install poetry
poetry install
cd ../..
```

### 4. Policy Engine (Rust)

```bash
cd services/policy-engine
cargo build --release
cd ../..
```

### 5. Web UI (React)

```bash
cd services/web-ui
npm install
cd ../..
```

### 6. TypeScript SDK (Optional)

```bash
cd libraries/sdk-typescript
npm install
npm run build
cd ../..
```

---

## Start the Platform

### Option 1: Automated Setup (Recommended)

```bash
# Make script executable
chmod +x scripts/dev-setup.sh

# Run setup script
./scripts/dev-setup.sh
```

This script will:
- Start PostgreSQL, Redis, Qdrant, ClickHouse
- Run database migrations
- Start all 4 core services + Web UI

### Option 2: Manual Startup

```bash
# Start infrastructure
docker-compose -f docker-compose.dev.yaml up -d postgres redis qdrant clickhouse

# Wait for databases to be ready
sleep 15

# Run migrations
docker-compose -f docker-compose.dev.yaml exec postgres \
  psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/001_initial_schema.sql

docker-compose -f docker-compose.dev.yaml exec postgres \
  psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/002_add_indexes.sql

# Start application services
docker-compose -f docker-compose.dev.yaml up -d
```

---

## Verify Installation

### 1. Check Docker Containers

```bash
docker-compose -f docker-compose.dev.yaml ps
```

Expected output: All services should show "Up" or "healthy"

### 2. Check Health Endpoints

```bash
# Gateway (Port 8080)
curl http://localhost:8080/health
# Expected: {"status":"healthy"}

# Identity (Port 3000)
curl http://localhost:3000/health
# Expected: {"status":"healthy"}

# Memory (Port 8000)
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Policy Engine (Port 8081)
curl http://localhost:8081/health
# Expected: {"status":"healthy"}
```

### 3. Access Web UI

Open your browser and navigate to:
```
http://localhost:3001
```

You should see the **Agent Economy OS Control Plane Dashboard**.

### 4. Check Database Connection

```bash
# PostgreSQL
docker-compose -f docker-compose.dev.yaml exec postgres psql -U postgres -d agentos -c "SELECT COUNT(*) FROM dids;"
# Should return: count | 0 (or more if you've registered agents)

# Redis
docker-compose -f docker-compose.dev.yaml exec redis redis-cli PING
# Should return: PONG
```

---

## Register Your First Agent

### Method 1: Web UI (Easiest)

1. **Open Browser**
   ```
   http://localhost:3001/register-agent
   ```

2. **Fill in Form:**
   - **Agent Type:** `assistant`
   - **Agent Name:** `my-first-agent`
   - **Description:** `My first test agent for learning the platform`
   - **Tags:** `demo, test, learning`
   - **Base Model:** `GPT-4` (select from dropdown)
   - **Temperature:** `0.7` (use slider)
   - **Max Tokens:** `4096`
   - **Cost Budget:** `100` (USD per hour)
   - **Rate Limit:** `1000` (calls per minute)

3. **Click "Deploy Agent"**
   - Wait for success message
   - DID will be generated automatically
   - Credential will be issued automatically

4. **Save Your Credentials:**
   - Copy the DID (format: `did:agent:abc-123-...`)
   - Copy the JWT token (will be needed for API calls)

### Method 2: API/CLI

#### Step 1: Create DID

```bash
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agentType": "assistant",
    "metadata": {
      "name": "my-first-agent",
      "description": "My first test agent",
      "tags": ["demo", "test"],
      "model": "GPT-4"
    }
  }' | jq
```

**Save the DID from response:**
```json
{
  "did": {
    "id": "did:agent:8d7f4a2b-...",
    "@context": ["https://www.w3.org/ns/did/v1"],
    ...
  }
}
```

#### Step 2: Issue Credential

```bash
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subjectDID": "did:agent:8d7f4a2b-...",
    "claims": {
      "capabilities": ["execute", "read", "write"],
      "role": "assistant",
      "model": "GPT-4"
    },
    "expiresIn": "30d"
  }' | jq
```

**Save the JWT token from response:**
```json
{
  "credential": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."
}
```

#### Step 3: Verify Registration

```bash
# List all registered agents
curl http://localhost:3000/api/v1/dids | jq

# Get specific agent details
curl http://localhost:3000/api/v1/dids/did:agent:8d7f4a2b-... | jq
```

---

## Test Agent Invocation

### 1. Simple Test Call

```bash
curl -X POST http://localhost:8080/a2a/v1/invoke \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_did": "did:agent:your-caller-id",
    "target_did": "did:agent:your-target-id",
    "action": "execute",
    "params": {
      "task": "hello_world",
      "message": "Test invocation"
    },
    "conversation_id": "test-conv-001",
    "credential": "YOUR_JWT_TOKEN"
  }' | jq
```

### 2. Store Memory

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_did": "did:agent:your-agent-id",
    "conversation_id": "test-conv-001",
    "content": "This is a test memory entry",
    "metadata": {
      "topic": "testing",
      "importance": "low"
    }
  }' | jq
```

### 3. Search Memories

```bash
curl "http://localhost:8000/api/v1/memories/search?agent_did=did:agent:your-agent-id&query=test&limit=10" | jq
```

### 4. Check Policy Evaluation

```bash
curl -X POST http://localhost:8081/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "caller_did": "did:agent:your-agent-id",
    "target_did": "did:agent:target-id",
    "action": "execute",
    "context": {}
  }' | jq
```

---

## Troubleshooting

### Services Won't Start

**Problem:** Docker containers fail to start

```bash
# Check logs for all services
docker-compose -f docker-compose.dev.yaml logs

# Check specific service
docker-compose -f docker-compose.dev.yaml logs gateway

# Restart specific service
docker-compose -f docker-compose.dev.yaml restart identity

# Clean restart everything
docker-compose -f docker-compose.dev.yaml down -v
./scripts/dev-setup.sh
```

### Database Connection Errors

**Problem:** Services can't connect to PostgreSQL

```bash
# Check if PostgreSQL is ready
docker-compose -f docker-compose.dev.yaml exec postgres pg_isready -U postgres

# Manually run migrations
docker-compose -f docker-compose.dev.yaml exec postgres \
  psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/001_initial_schema.sql

# Check database exists
docker-compose -f docker-compose.dev.yaml exec postgres \
  psql -U postgres -c "\l"
```

### Port Already in Use

**Problem:** Port conflict (e.g., port 8080 already in use)

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or edit docker-compose.dev.yaml to use different ports
```

### Web UI Not Loading

**Problem:** UI shows blank page or errors

```bash
cd services/web-ui

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Start dev server manually
npm run dev

# Access at http://localhost:5173 (Vite dev server)
```

### Permission Denied Errors

**Problem:** Script permission issues

```bash
# Make all scripts executable
chmod +x scripts/*.sh

# Run with sudo if needed (Linux)
sudo ./scripts/dev-setup.sh
```

### Memory Service Import Errors

**Problem:** Python import errors

```bash
cd services/memory

# Reinstall with Poetry
poetry install --no-cache

# Or use pip directly
pip install -r requirements.txt
```

---

## Next Steps

### 1. Explore the Dashboard

- Navigate to `http://localhost:3001`
- View metrics and agent activity
- Monitor costs and performance

### 2. Register More Agents

- Try different agent types (classifier, analyzer, orchestrator)
- Experiment with different models (Claude, Gemini)
- Configure various policies and limits

### 3. Build Multi-Agent Workflows

- Create agent-to-agent communication patterns
- Implement orchestrator agents
- Use shared memory for context

### 4. Monitor and Debug

- View live call graphs
- Check distributed traces
- Analyze memory usage
- Review security audit logs

### 5. Deploy to Production

When ready for production:

```bash
# Build production images
./scripts/build-images.sh

# Deploy to Kubernetes
./scripts/deploy-k8s.sh
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for full production guide.

---

## Quick Reference

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Web UI | http://localhost:3001 | Dashboard & Management |
| Gateway | http://localhost:8080 | Agent-to-Agent Communication |
| Identity | http://localhost:3000 | DID & Credential Management |
| Memory | http://localhost:8000 | Vector Storage & Context |
| Policy | http://localhost:8081 | Rate Limiting & Access Control |

### Common Commands

```bash
# Start everything
./scripts/dev-setup.sh

# Stop everything
docker-compose -f docker-compose.dev.yaml down

# View logs
docker-compose -f docker-compose.dev.yaml logs -f

# Restart service
docker-compose -f docker-compose.dev.yaml restart <service>

# Run tests
./scripts/test-all.sh

# Build images
./scripts/build-images.sh
```

### Database Access

```bash
# PostgreSQL
docker-compose -f docker-compose.dev.yaml exec postgres \
  psql -U postgres -d agentos

# Redis
docker-compose -f docker-compose.dev.yaml exec redis redis-cli

# View DIDs
docker-compose -f docker-compose.dev.yaml exec postgres \
  psql -U postgres -d agentos -c "SELECT id, document->>'metadata' FROM dids;"
```

---

## Support & Resources

- **Documentation:** [docs/](docs/)
- **API Reference:** [docs/API.md](docs/API.md)
- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Deployment:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Status Check Script

Save this as `check-status.sh` for quick health checks:

```bash
#!/bin/bash
echo "=== Agent Economy OS Status Check ==="
echo ""
echo "Services:"
echo "  Gateway:   $(curl -s http://localhost:8080/health | jq -r .status)"
echo "  Identity:  $(curl -s http://localhost:3000/health | jq -r .status)"
echo "  Memory:    $(curl -s http://localhost:8000/health | jq -r .status)"
echo "  Policy:    $(curl -s http://localhost:8081/health | jq -r .status)"
echo ""
echo "Agents Registered:"
curl -s http://localhost:3000/api/v1/dids?limit=10 | jq '.documents | length'
echo ""
echo "Web UI: http://localhost:3001"
```

---

**Version:** 0.1.0  
**Last Updated:** October 25, 2025  
**Status:** ✅ Production Ready
