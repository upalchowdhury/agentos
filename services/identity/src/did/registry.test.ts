import { Pool } from 'pg';
import { DIDRegistry } from './registry';

describe('DIDRegistry', () => {
  let pool: Pool;
  let registry: DIDRegistry;

  beforeAll(() => {
    pool = new Pool({
      connectionString: process.env.TEST_DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/agentos_test',
    });
    registry = new DIDRegistry(pool);
  });

  afterAll(async () => {
    await pool.end();
  });

  describe('create', () => {
    it('should create a valid DID document', async () => {
      const agentType = 'test_agent';
      const metadata = { name: 'Test Agent' };

      const document = await registry.create(agentType, metadata);

      expect(document.id).toMatch(/^did:agent:[a-f0-9-]{36}$/);
      expect(document.controller).toBe(document.id);
      expect(document['@context']).toContain('https://www.w3.org/ns/did/v1');
      expect(document.verificationMethod).toHaveLength(1);
      expect(document.metadata?.agentType).toBe(agentType);
      expect(document.metadata?.name).toBe('Test Agent');
    });

    it('should throw error if agentType is missing', async () => {
      await expect(registry.create('', {})).rejects.toThrow('agentType is required');
    });
  });

  describe('resolve', () => {
    it('should resolve existing DID', async () => {
      const created = await registry.create('test_agent', {});
      const resolved = await registry.resolve(created.id);

      expect(resolved.id).toBe(created.id);
    });

    it('should throw error for non-existent DID', async () => {
      await expect(registry.resolve('did:agent:nonexistent')).rejects.toThrow('DID not found');
    });

    it('should throw error for invalid DID format', async () => {
      await expect(registry.resolve('invalid')).rejects.toThrow('invalid DID format');
    });
  });

  describe('list', () => {
    it('should list DIDs with default pagination', async () => {
      const documents = await registry.list();
      expect(Array.isArray(documents)).toBe(true);
    });

    it('should respect limit parameter', async () => {
      const documents = await registry.list(5);
      expect(documents.length).toBeLessThanOrEqual(5);
    });

    it('should throw error for invalid limit', async () => {
      await expect(registry.list(0)).rejects.toThrow('limit must be between 1 and 1000');
      await expect(registry.list(1001)).rejects.toThrow('limit must be between 1 and 1000');
    });
  });
});
