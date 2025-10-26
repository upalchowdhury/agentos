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

  // Dashboard stats
  dashboard: {
    getStats: async () => {
      const response = await api.get('/identity/dashboard/stats');
      return response.data;
    },
  },

  // Runtime Service
  runtime: {
    deploy: (data: {
      agent_id: string;
      code: string;
      requirements: string[];
      environment: Record<string, string> | null;
      max_memory: string;
      max_cpu: string;
    }) => api.post('/v1/agents/deploy', data),

    invoke: (data: {
      agent_id: string;
      input_data: Record<string, any>;
      timeout: number;
    }) => api.post('/v1/agents/invoke', data),

    getStatus: (agentId: string) =>
      api.get(`/v1/agents/${agentId}/status`),

    delete: (agentId: string) =>
      api.delete(`/v1/agents/${agentId}`),
  },
};

export default api;
