import axios, { AxiosInstance } from 'axios';

export interface AgentOSConfig {
  apiUrl: string;
  agentDID: string;
  credential: string;
  timeout?: number;
}

export interface InvokeAgentRequest {
  targetDID: string;
  action: string;
  params: Record<string, unknown>;
  conversationID?: string;
}

export interface InvokeAgentResponse {
  success: boolean;
  data: Record<string, unknown>;
  error?: string;
}

export interface MemorySearchResult {
  memory_id: string;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export class AgentOSClient {
  private client: AxiosInstance;
  private agentDID: string;
  private credential: string;

  constructor(config: AgentOSConfig) {
    if (!config.apiUrl) throw new Error('apiUrl is required');
    if (!config.agentDID) throw new Error('agentDID is required');
    if (!config.credential) throw new Error('credential is required');

    this.agentDID = config.agentDID;
    this.credential = config.credential;

    this.client = axios.create({
      baseURL: config.apiUrl,
      timeout: config.timeout || 30000,
      headers: {
        Authorization: `Bearer ${config.credential}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async invokeAgent(request: InvokeAgentRequest): Promise<InvokeAgentResponse> {
    const response = await this.client.post<InvokeAgentResponse>('/a2a/v1/invoke', {
      caller_did: this.agentDID,
      target_did: request.targetDID,
      action: request.action,
      params: request.params,
      conversation_id: request.conversationID || this.generateConversationID(),
      credential: this.credential,
    });
    return response.data;
  }

  async storeMemory(
    content: string,
    conversationID: string,
    metadata: Record<string, unknown> = {}
  ): Promise<string> {
    const response = await this.client.post<{ memory_id: string }>('/api/v1/memories', {
      agent_did: this.agentDID,
      conversation_id: conversationID,
      content,
      metadata,
    });
    return response.data.memory_id;
  }

  async searchMemories(
    query: string,
    conversationID?: string,
    limit: number = 10
  ): Promise<MemorySearchResult[]> {
    const response = await this.client.get<{ results: MemorySearchResult[] }>(
      '/api/v1/memories/search',
      {
        params: {
          agent_did: this.agentDID,
          conversation_id: conversationID,
          query,
          limit,
        },
      }
    );
    return response.data.results;
  }

  private generateConversationID(): string {
    return `${this.agentDID}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  }
}
