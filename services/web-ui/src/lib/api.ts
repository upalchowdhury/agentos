import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('agentos_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API client for all services
export const agentAPI = {
  // Identity Service
  identity: {
    createDID: (data: { agentType: string; metadata: Record<string, unknown> }) =>
      api.post('/identity/dids', data),
    
    getDID: (did: string) =>
      api.get(`/identity/dids/${did}`),
    
    listDIDs: (limit = 100, offset = 0) =>
      api.get('/identity/dids', { params: { limit, offset } }),
    
    issueCredential: (data: { subjectDID: string; claims: Record<string, unknown>; expiresIn?: string }) =>
      api.post('/identity/credentials/issue', data),
    
    verifyCredential: (credential: string) =>
      api.post('/identity/credentials/verify', { credential }),
  },

  // Memory Service
  memory: {
    storeMemory: (data: {
      agent_did: string;
      conversation_id: string;
      content: string;
      metadata?: Record<string, unknown>;
    }) => api.post('/memory/memories', data),
    
    searchMemories: (params: {
      agent_did: string;
      conversation_id?: string;
      query?: string;
      limit?: number;
    }) => api.get('/memory/memories/search', { params }),
    
    getContext: (conversationId: string, agentDid: string, limit = 50) =>
      api.get(`/memory/context/${conversationId}`, {
        params: { agent_did: agentDid, limit },
      }),
    
    storeInteraction: (data: {
      caller_did: string;
      target_did: string;
      conversation_id: string;
      request: Record<string, unknown>;
      response: Record<string, unknown>;
    }) => api.post('/memory/interactions', data),
  },

  // Policy Engine
  policy: {
    evaluate: (data: {
      caller_did: string;
      target_did: string;
      action: string;
      context: Record<string, unknown>;
    }) => api.post('/policy/evaluate', data),
    
    addRule: (rule: {
      type: 'RateLimit' | 'CostLimit';
      max_requests?: number;
      window_seconds?: number;
      max_cost_cents?: number;
    }) => api.post('/policy/rules', rule),
    
    recordCost: (data: {
      caller_did: string;
      cost_cents: number;
      window_seconds: number;
    }) => api.post('/policy/cost', data),
  },

  // Gateway Service
  gateway: {
    invokeAgent: (data: {
      caller_did: string;
      target_did: string;
      action: string;
      params: Record<string, unknown>;
      conversation_id?: string;
      credential: string;
      context?: Record<string, unknown>;
    }) => api.post('/gateway/a2a/v1/invoke', data),
    
    health: () => api.get('/gateway/health'),
  },

  // Dashboard stats (mock for now - would come from observability service)
  dashboard: {
    getMetrics: async () => {
      // In production, this would query ClickHouse/Prometheus
      return {
        activeAgents: 127,
        throughput: 1234,
        cost: 847,
        alerts: 3,
      };
    },
    
    getAgentStats: async () => {
      // Mock data - in production, aggregate from interactions table
      return [
        {
          name: 'fraud-detector-v2',
          status: 'critical',
          calls: 23441,
          cost: 847,
          latency: 156,
          errorRate: 0.3,
        },
        {
          name: 'customer-support-orchestrator',
          status: 'healthy',
          calls: 18923,
          cost: 234,
          latency: 289,
          errorRate: 0.1,
        },
      ];
    },
  },
};

export default api;
