# Dashboard with Real Data - Setup Complete!

## What Was Fixed

You noticed the dashboard was showing **hardcoded mock data**. I've now implemented **real dashboard functionality** that pulls actual data from your PostgreSQL database.

## Changes Made

### 1. Backend: Identity Service Dashboard Endpoint
**File**: `services/identity/src/server.ts`

Added new endpoint: `GET /api/v1/dashboard/stats`

Returns:
```json
{
  "summary": {
    "total_agents": "5",
    "active_credentials": "0",
    "role_assignments": "0",
    "agents_with_roles": "0",
    "violations_24h": "0"
  },
  "agentsByType": [
    {"agent_type": "test", "count": "5"}
  ],
  "recentAgents": [...],
  "roleStats": [...]
}
```

### 2. Frontend: Updated Web UI
**Files**:
- `services/web-ui/src/lib/api.ts` - Changed from mock data to real API calls
- `services/web-ui/src/components/Dashboard.tsx` - Updated to display real data

### 3. Database Migration
Applied RBAC schema migration (`003_rbac_schema.sql`) which adds:
- `roles` table with 4 default roles
- `permissions` table  
- `agent_roles` table (many-to-many)
- `content_violations` table

## Current Dashboard Metrics

### Live Data Shown:
- **Total Agents**: 5 (from your testing)
- **Active Credentials**: 0
- **Role Assignments**: 0  
- **Content Violations (24h)**: 0

### Recent Agents Table:
Shows your 5 test agents created with:
- DID (truncated)
- Type badge (test)
- Name from metadata
- Creation timestamp

### Role Distribution:
- agent:basic (0 agents)
- agent:executor (0 agents)
- agent:orchestrator (0 agents)
- agent:admin (0 agents)

## Access the Dashboard

### Option 1: Port Forward (Direct Access)
```bash
# Forward Web UI
kubectl port-forward -n agentos svc/web-ui 3001:80

# Open browser
open http://localhost:3001
```

### Option 2: API Only
```bash
# Forward Identity service
kubectl port-forward -n agentos svc/identity 3000:3000

# Test dashboard endpoint
curl http://localhost:3000/api/v1/dashboard/stats | jq
```

## Testing the Dashboard

### 1. Create More Agents
```bash
kubectl port-forward -n agentos svc/identity 3000:3000 &

curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{
    "agentType": "autonomous",
    "metadata": {
      "name": "Customer Support Bot",
      "description": "Handles customer inquiries",
      "agentType": "autonomous"
    }
  }'
```

### 2. Assign Roles
```bash
# Get agent DID from previous response
curl -X POST http://localhost:3000/api/v1/rbac/roles/assign \
  -H "Content-Type: application/json" \
  -d '{
    "agentDID": "did:agent:YOUR_DID_HERE",
    "roleName": "agent:executor"
  }'
```

### 3. Issue Credentials
```bash
curl -X POST http://localhost:3000/api/v1/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "subjectDID": "did:agent:YOUR_DID_HERE",
    "claims": {
      "role": "executor",
      "permissions": ["read", "write"]
    },
    "expiresIn": "30d"
  }'
```

### 4. Refresh Dashboard
The dashboard auto-refreshes every 10 seconds, so your new data will appear automatically!

## Dashboard Features

### Metric Cards (Top Row)
1. **Total Agents** (Blue) - Count of all registered DIDs
2. **Active Credentials** (Green) - Non-revoked verifiable credentials
3. **Role Assignments** (Orange) - RBAC role assignments
4. **Violations (24h)** (Red) - Content policy violations

### Recent Agents Table
- Shows 10 most recent agents
- Displays DID, Type, Name, Creation time
- Color-coded type badges

### Role Distribution Section
- Lists all available roles
- Shows agent count for each role
- Updates as you assign roles

## API Endpoints

All functional endpoints in the Identity service:

### DIDs
- `POST /api/v1/dids` - Create new agent DID
- `GET /api/v1/dids/:did` - Get DID document
- `GET /api/v1/dids` - List all DIDs

### Credentials
- `POST /api/v1/credentials/issue` - Issue credential
- `POST /api/v1/credentials/verify` - Verify credential
- `POST /api/v1/credentials/revoke` - Revoke credential

### RBAC
- `POST /api/v1/rbac/roles/assign` - Assign role to agent
- `POST /api/v1/rbac/roles/revoke` - Revoke role
- `GET /api/v1/rbac/roles/:agentDID` - Get agent roles
- `POST /api/v1/rbac/check` - Check permissions
- `GET /api/v1/rbac/roles` - List all roles

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard metrics (NEW!)

## Troubleshooting

### Dashboard shows 0s everywhere
- No agents created yet - use the "Register Agent" page or API
- Database connection issue - check postgres logs

### Port forward not working
```bash
# Kill existing port forwards
pkill -f "port-forward"

# Restart
kubectl port-forward -n agentos svc/web-ui 3001:80
```

### Dashboard not updating
- Check browser console for errors
- Verify nginx proxy config in web-ui pod
- Check identity service logs:
  ```bash
  kubectl logs -n agentos -l app=identity -f
  ```

## Current Deployment Status

```
✅ PostgreSQL (with RBAC schema)
✅ Redis  
✅ Identity Service (with dashboard endpoint)
✅ Gateway
✅ Web UI (with real data display)
```

## Next Steps

1. **Create diverse agents** - Use different agentTypes (autonomous, semi_autonomous, human_in_loop, proxy)
2. **Assign RBAC roles** - Test permission system
3. **Issue credentials** - See active credentials count increase
4. **Test content filtering** - Trigger violations to see them on dashboard
5. **Deploy Memory + Policy services** - Add more functionality

## Quick Demo Script

```bash
# 1. Port forward
kubectl port-forward -n agentos svc/identity 3000:3000 &
kubectl port-forward -n agentos svc/web-ui 3001:80 &

# 2. Create 3 different agents
curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{"agentType":"autonomous","metadata":{"name":"ML Model Agent","agentType":"autonomous"}}'

curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{"agentType":"semi_autonomous","metadata":{"name":"Approval Bot","agentType":"semi_autonomous"}}'

curl -X POST http://localhost:3000/api/v1/dids \
  -H "Content-Type: application/json" \
  -d '{"agentType":"human_in_loop","metadata":{"name":"Support Assistant","agentType":"human_in_loop"}}'

# 3. Open dashboard
open http://localhost:3001

# Watch the numbers update!
```

---

**The dashboard now shows REAL data from your production database!** 🎉
