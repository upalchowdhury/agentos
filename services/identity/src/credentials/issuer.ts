import { Pool } from 'pg';
import * as jose from 'jose';
import { JWTPayload } from '../types';

export class CredentialIssuer {
  constructor(private pool: Pool) {}

  async issue(
    subjectDID: string,
    claims: Record<string, unknown>,
    expiresIn: string = '30d'
  ): Promise<string> {
    if (!subjectDID || !subjectDID.startsWith('did:')) {
      throw new Error('invalid subject DID');
    }

    const now = Math.floor(Date.now() / 1000);
    const exp = now + this.parseExpiry(expiresIn);

    const payload: JWTPayload = {
      iss: 'did:agent:issuer',
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
    const jwt = await new jose.SignJWT(payload as unknown as jose.JWTPayload)
      .setProtectedHeader({ alg: 'EdDSA' })
      .sign(privateKey);

    // Store credential record
    const query = `
      INSERT INTO credentials (id, subject_did, jwt, issued_at, expires_at) 
      VALUES (gen_random_uuid(), $1, $2, to_timestamp($3), to_timestamp($4))
    `;
    await this.pool.query(query, [subjectDID, jwt, now, exp]);

    return jwt;
  }

  private parseExpiry(expiresIn: string): number {
    const match = expiresIn.match(/^(\d+)([dhm])$/);
    if (!match) {
      throw new Error('invalid expiry format (use format: 30d, 24h, 60m)');
    }

    const value = parseInt(match[1], 10);
    const unit = match[2];

    switch (unit) {
      case 'd':
        return value * 86400;
      case 'h':
        return value * 3600;
      case 'm':
        return value * 60;
      default:
        throw new Error('invalid time unit');
    }
  }

  private async getIssuerPrivateKey(): Promise<jose.KeyLike> {
    const jwkString = process.env.ISSUER_PRIVATE_KEY;
    if (!jwkString) {
      // For development, generate a temporary key
      const { privateKey } = await jose.generateKeyPair('EdDSA');
      return privateKey;
    }

    const jwk = JSON.parse(jwkString);
    return (await jose.importJWK(jwk)) as jose.KeyLike;
  }
}
