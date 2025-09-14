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

// Chat API
export const chatAPI = {
  getConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get('/api/chat/conversations');
    return response.data;
  },

  createConversation: async (title: string): Promise<Conversation> => {
    const response = await apiClient.post('/api/chat/conversations', { title });
    return response.data;
  },

  getModels: async (): Promise<{ models: AIModel[]; external_apis: Record<string, string> }> => {
    const response = await apiClient.get('/api/chat/models');
    return response.data;
  },

  getChatCapabilities: async (): Promise<{
    features: string[];
    models_available: number;
    external_apis: number;
    real_time_data: boolean;
    streaming: boolean;
  }> => {
    const response = await apiClient.get('/api/chat/capabilities');
    return response.data;
  },

  // Streaming chat with Server-Sent Events
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
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
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

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'content') {
                onChunk(data.content);
              } else if (data.type === 'done') {
                onComplete(data);
                return;
              } else if (data.type === 'error') {
                onError(data.content);
                return;
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error occurred');
    }
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