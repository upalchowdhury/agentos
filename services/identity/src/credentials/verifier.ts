import { Pool } from 'pg';
import * as jose from 'jose';
import { JWTPayload } from '../types';

export class CredentialVerifier {
  constructor(private pool: Pool) {}

  async verify(credential: string): Promise<{ valid: boolean; did?: string; reason?: string }> {
    if (!credential) {
      return { valid: false, reason: 'credential required' };
    }

    try {
      // Get issuer public key
      const publicKey = await this.getIssuerPublicKey();

      // Verify JWT signature and expiration
      const { payload } = await jose.jwtVerify(credential, publicKey, {
        issuer: 'did:agent:issuer',
      });

      const jwtPayload = payload as unknown as JWTPayload;

      // Check if credential is revoked
      const revoked = await this.isRevoked(credential);
      if (revoked) {
        return { valid: false, reason: 'credential revoked' };
      }

      return {
        valid: true,
        did: jwtPayload.sub,
      };
    } catch (error) {
      if (error instanceof Error) {
        return { valid: false, reason: error.message };
      }
      return { valid: false, reason: 'verification failed' };
    }
  }

  async revoke(credential: string): Promise<void> {
    if (!credential) {
      throw new Error('credential required');
    }

    const query = 'UPDATE credentials SET revoked_at = NOW() WHERE jwt = $1';
    const result = await this.pool.query(query, [credential]);

    if (result.rowCount === 0) {
      throw new Error('credential not found');
    }
  }

  private async isRevoked(credential: string): Promise<boolean> {
    const query = 'SELECT revoked_at FROM credentials WHERE jwt = $1';
    const result = await this.pool.query(query, [credential]);

    if (result.rows.length === 0) {
      return false;
    }

    return result.rows[0].revoked_at !== null;
  }

  private async getIssuerPublicKey(): Promise<jose.KeyLike> {
    const jwkString = process.env.ISSUER_PRIVATE_KEY;
    if (!jwkString) {
      // For development, generate a temporary key pair
      const { publicKey } = await jose.generateKeyPair('EdDSA');
      return publicKey;
    }

    const jwk = JSON.parse(jwkString);
    return (await jose.importJWK(jwk)) as jose.KeyLike;
  }
}
