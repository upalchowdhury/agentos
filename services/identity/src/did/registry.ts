import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';
import { DIDDocument } from '../types';
import * as crypto from 'crypto';

export class DIDRegistry {
  constructor(private pool: Pool) {}

  async create(agentType: string, metadata: Record<string, unknown> = {}): Promise<DIDDocument> {
    if (!agentType) {
      throw new Error('agentType is required');
    }

    const id = `did:agent:${uuidv4()}`;
    const publicKey = this.generateKeyPair();

    const document: DIDDocument = {
      '@context': ['https://www.w3.org/ns/did/v1'],
      id,
      controller: id,
      verificationMethod: [
        {
          id: `${id}#key-1`,
          type: 'Ed25519VerificationKey2020',
          controller: id,
          publicKeyMultibase: publicKey,
        },
      ],
      authentication: [`${id}#key-1`],
      assertionMethod: [`${id}#key-1`],
      metadata: {
        agentType,
        ...metadata,
        created: new Date().toISOString(),
      },
    };

    const query = 'INSERT INTO dids (id, document, created_at) VALUES ($1, $2, NOW()) RETURNING *';
    await this.pool.query(query, [id, JSON.stringify(document)]);

    return document;
  }

  async resolve(did: string): Promise<DIDDocument> {
    if (!did || !did.startsWith('did:')) {
      throw new Error('invalid DID format');
    }

    const query = 'SELECT document FROM dids WHERE id = $1';
    const result = await this.pool.query(query, [did]);

    if (result.rows.length === 0) {
      throw new Error('DID not found');
    }

    return result.rows[0].document as DIDDocument;
  }

  async list(limit: number = 100, offset: number = 0): Promise<DIDDocument[]> {
    if (limit < 1 || limit > 1000) {
      throw new Error('limit must be between 1 and 1000');
    }

    const query = 'SELECT document FROM dids ORDER BY created_at DESC LIMIT $1 OFFSET $2';
    const result = await this.pool.query(query, [limit, offset]);

    return result.rows.map((row) => row.document as DIDDocument);
  }

  private generateKeyPair(): string {
    // Generate Ed25519 key pair
    // In production, use proper key generation and storage
    const randomBytes = crypto.randomBytes(32);
    return 'z' + randomBytes.toString('base64url');
  }
}
