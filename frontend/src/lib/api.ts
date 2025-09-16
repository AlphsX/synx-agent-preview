// API Client for Checkmate Spec Preview
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    // Use demo token for development/testing
    config.headers.Authorization = `Bearer demo-token`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  model?: string;
}

export interface Conversation {
  id: string;
  title: string;
  last_message?: string;
  created_at: string;
}

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  description: string;
  features?: string[];
  recommended?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

// Authentication API
export const authAPI = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post('/api/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  register: async (email: string, username: string, password: string): Promise<User> => {
    const response = await apiClient.post('/api/auth/register', {
      email,
      username,
      password
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  }
};

// Enhanced Chat API
export const chatAPI = {
  getConversations: async (): Promise<Conversation[]> => {
    try {
      const response = await apiClient.get('/api/chat/conversations');
      return response.data;
    } catch (error) {
      console.warn('Enhanced chat conversations endpoint not available:', error);
      return [];
    }
  },

  createConversation: async (title: string): Promise<Conversation> => {
    try {
      const response = await apiClient.post('/api/chat/conversations', { title });
      return response.data;
    } catch (error) {
      console.warn('Enhanced chat create conversation endpoint not available:', error);
      throw error;
    }
  },

  getModels: async (): Promise<{ models: AIModel[]; total_models: number; providers: string[]; enhanced_features: string[] }> => {
    try {
      const response = await apiClient.get('/api/chat/models');
      return response.data;
    } catch (error) {
      console.warn('Enhanced chat models endpoint not available:', error);
      // Return fallback models
      const fallbackModels: AIModel[] = [
        { id: 'openai/gpt-oss-120b', name: 'GPT OSS 120B', provider: 'Groq', description: 'OpenAI\'s GPT OSS 120B model for advanced reasoning', recommended: true },
        { id: 'meta-llama/llama-4-maverick-17b-128e-instruct', name: 'Llama 4 Maverick 17B', provider: 'Groq', description: 'Meta\'s Llama 4 Maverick 17B instruction-tuned model' },
        { id: 'deepseek-r1-distill-llama-70b', name: 'DeepSeek R1 Distill Llama 70B', provider: 'Groq', description: 'DeepSeek\'s R1 distilled Llama 70B model' },
        { id: 'qwen/qwen3-32b', name: 'Qwen 3 32B', provider: 'Groq', description: 'Alibaba\'s Qwen 3 32B model for multilingual tasks' },
        { id: 'moonshotai/kimi-k2-instruct-0905', name: 'Kimi K2 Instruct', provider: 'Groq', description: 'MoonshotAI\'s Kimi K2 instruction-tuned model' }
      ];
      return {
        models: fallbackModels,
        total_models: fallbackModels.length,
        providers: ['Groq'],
        enhanced_features: ['real_time_web_search', 'cryptocurrency_data', 'news_updates', 'vector_knowledge_search']
      };
    }
  },

  getChatCapabilities: async (): Promise<{
    features: string[];
    models_available: number;
    ai_providers: number;
    search_providers: number;
    external_apis: number;
    real_time_data: boolean;
    streaming: boolean;
    caching: boolean;
    fallback_support: boolean;
  }> => {
    try {
      const response = await apiClient.get('/api/chat/capabilities');
      return response.data;
    } catch (error) {
      console.warn('Enhanced chat capabilities endpoint not available:', error);
      return {
        features: ['Multi-AI model support', 'Real-time web search', 'Cryptocurrency data', 'News updates', 'Vector search'],
        models_available: 5,
        ai_providers: 1,
        search_providers: 2,
        external_apis: 3,
        real_time_data: true,
        streaming: true,
        caching: true,
        fallback_support: true
      };
    }
  },

  getSearchTools: async (): Promise<{
    tools: Array<{
      id: string;
      name: string;
      description: string;
      providers: string[];
      primary_provider: string;
      available: boolean;
    }>;
    search_providers_status: Record<string, unknown>;
    intelligent_routing: boolean;
    fallback_support: boolean;
  }> => {
    try {
      const response = await apiClient.get('/api/chat/search-tools');
      return response.data;
    } catch (error) {
      console.warn('Enhanced chat search tools endpoint not available:', error);
      return {
        tools: [
          { id: 'web_search', name: 'Web Search', description: 'Search the web for current information', providers: ['SerpAPI', 'Brave Search'], primary_provider: 'SerpAPI', available: true },
          { id: 'news_search', name: 'News Search', description: 'Search for latest news and current events', providers: ['SerpAPI', 'Brave Search'], primary_provider: 'SerpAPI', available: true },
          { id: 'crypto_data', name: 'Cryptocurrency Data', description: 'Get real-time cryptocurrency market data', providers: ['Binance'], primary_provider: 'Binance', available: true },
          { id: 'vector_search', name: 'Knowledge Search', description: 'Search domain-specific knowledge base', providers: ['Vector Database'], primary_provider: 'PostgreSQL + pgvector', available: true }
        ],
        search_providers_status: {},
        intelligent_routing: true,
        fallback_support: true
      };
    }
  },

  getServiceStatus: async (): Promise<{
    service: string;
    status: string;
    timestamp: string;
    services: Record<string, unknown>;
    active_connections: number;
    features: Record<string, string>;
  }> => {
    try {
      const response = await apiClient.get('/api/chat/status');
      return response.data;
    } catch (error) {
      console.warn('Enhanced chat status endpoint not available:', error);
      return {
        service: 'Enhanced Chat Service',
        status: 'demo_mode',
        timestamp: new Date().toISOString(),
        services: {},
        active_connections: 0,
        features: {
          'ai_models': 'Demo mode - configure API keys',
          'web_search': 'Demo mode - configure SerpAPI',
          'crypto_data': 'Demo mode - configure Binance API'
        }
      };
    }
  },

  // Enhanced streaming chat with Server-Sent Events
  streamChat: async (
    conversationId: string,
    message: string,
    modelId: string,
    onChunk: (chunk: string) => void,
    onComplete: (data: unknown) => void,
    onError: (error: string) => void
  ): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || 'demo-token'}`,
        },
        body: JSON.stringify({
          content: message,
          role: 'user',
          model_id: modelId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body reader available');
      }

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') {
              onComplete({ type: 'done' });
              return;
            }
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'content' || data.content) {
                onChunk(data.content || data.text || '');
              } else if (data.type === 'done') {
                onComplete(data);
                return;
              } else if (data.type === 'error') {
                onError(data.content || data.message || 'Stream error');
                return;
              }
            } catch (parseError) {
              // If it's not JSON, treat as plain text content
              if (dataStr && dataStr !== '[DONE]') {
                onChunk(dataStr);
              }
            }
          }
        }
      }
      
      // Handle any remaining buffer content
      if (buffer.trim()) {
        onComplete({ type: 'done' });
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  },

  // WebSocket streaming alternative
  connectWebSocket: (
    conversationId: string,
    onMessage: (data: Record<string, unknown>) => void,
    onError: (error: string) => void,
    onClose: () => void
  ): WebSocket => {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/chat/ws/${conversationId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Enhanced WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch {
        console.warn('Failed to parse WebSocket message:', event.data);
        // Handle plain text messages
        onMessage({ type: 'content', content: event.data });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('Enhanced WebSocket disconnected');
      onClose();
    };

    return ws;
  },

  // Search endpoints
  searchWeb: async (query: string, count: number = 10, provider?: string) => {
    const params = new URLSearchParams({ query, count: count.toString() });
    if (provider) params.append('provider', provider);
    
    const response = await apiClient.post(`/api/chat/search/web?${params}`);
    return response.data;
  },

  searchNews: async (query: string, count: number = 5, timePeriod: string = '1d', provider?: string) => {
    const params = new URLSearchParams({ 
      query, 
      count: count.toString(),
      time_period: timePeriod
    });
    if (provider) params.append('provider', provider);
    
    const response = await apiClient.post(`/api/chat/search/news?${params}`);
    return response.data;
  },

  getCryptoMarket: async () => {
    const response = await apiClient.get('/api/chat/crypto/market');
    return response.data;
  }
};

// External APIs
export const externalAPI = {
  searchWeb: async (query: string, count: number = 10) => {
    const response = await apiClient.get('/api/external/search', {
      params: { query, count }
    });
    return response.data;
  },

  searchNews: async (query: string, count: number = 5) => {
    const response = await apiClient.get('/api/external/search/news', {
      params: { query, count }
    });
    return response.data;
  },

  getCryptoMarket: async () => {
    const response = await apiClient.get('/api/external/crypto/market');
    return response.data;
  },

  getCryptoPrice: async (symbol: string) => {
    const response = await apiClient.get(`/api/external/crypto/price/${symbol}`);
    return response.data;
  },

  getTrendingCrypto: async () => {
    const response = await apiClient.get('/api/external/crypto/trending');
    return response.data;
  },

  getApiHealth: async () => {
    const response = await apiClient.get('/api/external/health');
    return response.data;
  }
};

// Health check
export const healthAPI = {
  checkHealth: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getStatus: async () => {
    const response = await apiClient.get('/api/status');
    return response.data;
  }
};

export default apiClient;