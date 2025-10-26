import express from 'express';
import { Pool } from 'pg';
import { trace } from '@opentelemetry/api';
import { DIDRegistry } from './did/registry';
import { CredentialIssuer } from './credentials/issuer';
import { CredentialVerifier } from './credentials/verifier';
import { RBACManager } from './rbac/roles';

const app = express();
app.use(express.json());

// Database connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/agentos',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

// Initialize services
const didRegistry = new DIDRegistry(pool);
const credentialIssuer = new CredentialIssuer(pool);
const credentialVerifier = new CredentialVerifier(pool);
const rbacManager = new RBACManager(pool);

// Routes

// Create DID
app.post('/api/v1/dids', async (req, res) => {
  const tracer = trace.getTracer('identity-service');
  const span = tracer.startSpan('create-did');

  try {
    const { agentType, metadata } = req.body;

    if (!agentType) {
      res.status(400).json({ error: 'agentType is required' });
      return;
    }

    const did = await didRegistry.create(agentType, metadata || {});

    span.setAttributes({
      'did.id': did.id,
      'did.type': agentType,
    });

    res.status(201).json({ did });
  } catch (error) {
    span.recordException(error as Error);
    res.status(500).json({ error: (error as Error).message });
  } finally {
    span.end();
  }
});

// Resolve DID
app.get('/api/v1/dids/:did', async (req, res) => {
  try {
    const { did } = req.params;
    const document = await didRegistry.resolve(did);
    res.json({ document });
  } catch (error) {
    const err = error as Error;
    if (err.message === 'DID not found') {
      res.status(404).json({ error: 'DID not found' });
    } else {
      res.status(400).json({ error: err.message });
    }
  }
});

// List DIDs
app.get('/api/v1/dids', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 100;
    const offset = parseInt(req.query.offset as string) || 0;
    
    const documents = await didRegistry.list(limit, offset);
    res.json({ documents, limit, offset });
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

// Issue credential
app.post('/api/v1/credentials/issue', async (req, res) => {
  try {
    const { subjectDID, claims, expiresIn } = req.body;

    if (!subjectDID || !claims) {
      res.status(400).json({ error: 'subjectDID and claims are required' });
      return;
    }

    const credential = await credentialIssuer.issue(
      subjectDID,
      claims,
      expiresIn || '30d'
    );

    res.status(201).json({ credential });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// Verify credential
app.post('/api/v1/credentials/verify', async (req, res) => {
  try {
    const { credential } = req.body;

    if (!credential) {
      res.status(400).json({ error: 'credential is required' });
      return;
    }

    const result = await credentialVerifier.verify(credential);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

// Revoke credential
app.post('/api/v1/credentials/revoke', async (req, res) => {
  try {
    const { credential } = req.body;

    if (!credential) {
      res.status(400).json({ error: 'credential is required' });
      return;
    }

    await credentialVerifier.revoke(credential);
    res.json({ status: 'revoked' });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// RBAC Endpoints
app.post('/api/v1/rbac/roles/assign', async (req, res) => {
  try {
    const { agentDID, roleName, grantedBy } = req.body;
    await rbacManager.assignRole(agentDID, roleName, grantedBy);
    res.json({ status: 'assigned' });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/api/v1/rbac/roles/revoke', async (req, res) => {
  try {
    const { agentDID, roleName } = req.body;
    await rbacManager.revokeRole(agentDID, roleName);
    res.json({ status: 'revoked' });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.get('/api/v1/rbac/roles/:agentDID', async (req, res) => {
  try {
    const { agentDID } = req.params;
    const roles = await rbacManager.getAgentRoles(agentDID);
    res.json({ roles });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/api/v1/rbac/check', async (req, res) => {
  try {
    const { agentDID, resource, action, context } = req.body;
    const allowed = await rbacManager.checkPermission(agentDID, resource, action, context);
    res.json({ allowed });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.get('/api/v1/rbac/roles', async (_req, res) => {
  try {
    const roles = await rbacManager.listAllRoles();
    res.json({ roles });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// Dashboard Stats
app.get('/api/v1/dashboard/stats', async (_req, res) => {
  try {
    const stats = await pool.query(`
      SELECT 
        (SELECT COUNT(*) FROM dids) as total_agents,
        (SELECT COUNT(*) FROM credentials WHERE NOT revoked) as active_credentials,
        (SELECT COUNT(*) FROM agent_roles) as role_assignments,
        (SELECT COUNT(DISTINCT agent_did) FROM agent_roles) as agents_with_roles,
        (SELECT COUNT(*) FROM content_violations WHERE created_at > NOW() - INTERVAL '24 hours') as violations_24h
    `);
    
    const agentsByType = await pool.query(`
      SELECT 
        COALESCE(document->'metadata'->>'agentType', 'unknown') as agent_type,
        COUNT(*) as count
      FROM dids
      GROUP BY document->'metadata'->>'agentType'
      ORDER BY count DESC
    `);
    
    const recentAgents = await pool.query(`
      SELECT 
        id,
        COALESCE(document->'metadata'->>'agentType', 'unknown') as agent_type,
        document->'metadata' as metadata,
        created_at
      FROM dids
      ORDER BY created_at DESC
      LIMIT 10
    `);
    
    const roleStats = await pool.query(`
      SELECT r.name, r.description, COUNT(ar.agent_did) as agent_count
      FROM roles r
      LEFT JOIN agent_roles ar ON r.name = ar.role_name
      GROUP BY r.name, r.description
      ORDER BY agent_count DESC
    `);

    res.json({
      summary: stats.rows[0],
      agentsByType: agentsByType.rows,
      recentAgents: recentAgents.rows,
      roleStats: roleStats.rows
    });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'healthy' });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Identity service listening on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing connections...');
  await pool.end();
  process.exit(0);
});
