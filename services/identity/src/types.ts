export interface DIDDocument {
  '@context': string[];
  id: string;
  controller: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  assertionMethod: string[];
  metadata?: {
    agentType: string;
    created: string;
    [key: string]: unknown;
  };
}

export interface VerificationMethod {
  id: string;
  type: string;
  controller: string;
  publicKeyMultibase: string;
}

export interface VerifiableCredential {
  '@context': string[];
  type: string[];
  credentialSubject: {
    id: string;
    [key: string]: unknown;
  };
}

export interface JWTPayload {
  iss: string;
  sub: string;
  iat: number;
  exp: number;
  vc: VerifiableCredential;
}
