// API Client for Checkmate Spec Preview
import axios from 'axios';

// API service for connecting to the backend AI services
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

interface AIModel {
  id: string;
  name: string;
  provider: string;
  description: string;
  features?: string[];
  recommended?: boolean;
}

export const chatAPI = {
  // Fetch available AI models from the backend
  getModels: async (): Promise<{ models: AIModel[] }> => {
    try {
      console.log('Fetching AI models from:', `${API_BASE_URL}/api/chat/models`);
      const response = await fetch(`${API_BASE_URL}/api/chat/models`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Successfully fetched models:', data);
      return { models: data.models || [] };
    } catch (error) {
      console.error('Error fetching AI models:', error);
      throw error;
    }
  },

  // Stream chat messages with the selected AI model
  streamChat: async (
    conversationId: string,
    message: string,
    modelId: string,
    onChunk: (chunk: string) => void,
    onComplete: (data: any) => void,
    onError: (error: string) => void
  ): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: message,
          model_id: modelId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.error) {
                  onError(data.error);
                  return;
                }
                
                if (data.type === 'done') {
                  onComplete(data);
                  return;
                }
                
                if (data.content) {
                  onChunk(data.content);
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line);
              }
            }
          }
        }
        
        onComplete({});
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Error in streamChat:', error);
      onError(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  },

  // Get search tools from the backend
  getSearchTools: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/search-tools`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch search tools: ${response.status} ${response.statusText}`);
      }
      
      const tools = await response.json();
      return tools;
    } catch (error) {
      console.error('Error fetching search tools:', error);
      throw error;
    }
  }
};

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