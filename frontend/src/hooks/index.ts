// Enhanced React hooks for Checkmate Spec Preview
import { useState, useEffect, useCallback, useRef } from 'react';
import { chatAPI, externalAPI, type Message, type AIModel, type Conversation } from '@/lib/api';

// Export dark mode hook
export { useDarkMode } from './useDarkMode';

// Export dynamic favicon hook
export { useDynamicFavicon } from './useDynamicFavicon';

// Export idle detection hook
export { useIdleDetection } from './useIdleDetection';

// Export keyboard shortcuts hook
export { useKeyboardShortcuts } from './useKeyboardShortcuts';

// Export swipe gesture hook
export { useSwipeGesture } from './useSwipeGesture';

// Export app loading hook
export { useAppLoading } from './useAppLoading';

// Export mobile detection hook
export { useMobileDetection } from './useTouchInteractions';

// Hook for managing chat state
export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [availableModels, setAvailableModels] = useState<AIModel[]>([
    { id: 'openai/gpt-oss-120b', name: 'GPT-OSS-120B', provider: 'OpenAI', description: 'Open source 120B parameter model' },
    { id: 'meta-llama/llama-4-maverick-17b-128e-instruct', name: 'Llama-4 Maverick 17B', provider: 'Meta', description: '17B parameter model with 128 experts' },
    { id: 'deepseek-r1-distill-llama-70b', name: 'DeepSeek R1 Distill Llama 70B', provider: 'DeepSeek', description: 'Distilled version of DeepSeek R1 with 70B parameters' },
    { id: 'qwen/qwen3-32b', name: 'Qwen3 32B', provider: 'Qwen', description: 'Latest Qwen model with 32B parameters' },
    { id: 'moonshotai/kimi-k2-instruct', name: 'Kimi K2 Instruct', provider: 'Moonshot AI', description: 'Kimi K2 instruction-following model' }
  ]);
  const [selectedModel, setSelectedModel] = useState('openai/gpt-oss-120b');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Load available models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const data = await chatAPI.getModels();
        setAvailableModels(data.models);
        
        // Set recommended model as default
        const recommended = data.models.find(m => m.recommended);
        if (recommended) {
          setSelectedModel(recommended.id);
        }
      } catch (error) {
        console.error('Failed to load models:', error);
      }
    };

    loadModels();
  }, []);

  // Load conversations
  const loadConversations = useCallback(async () => {
    try {
      const data = await chatAPI.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, []);

  // Send message with enhanced streaming
  const sendMessage = useCallback(async (content: string, conversationId?: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setCurrentResponse('');

    const activeConvId = conversationId || activeConversationId || 'default';

    try {
      let assistantMessage = '';
      
      await chatAPI.streamChat(
        activeConvId,
        content,
        selectedModel,
        // On chunk received
        (chunk: string) => {
          assistantMessage += chunk;
          setCurrentResponse(assistantMessage);
        },
        // On complete
        (data: unknown) => {
          const finalMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: assistantMessage,
            role: 'assistant',
            timestamp: new Date(),
            model: selectedModel
          };
          
          setMessages(prev => [...prev, finalMessage]);
          setCurrentResponse('');
          setIsLoading(false);
        },
        // On error
        (error: string) => {
          console.error('Chat error:', error);
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: `Error: ${error}`,
            role: 'assistant',
            timestamp: new Date(),
            model: selectedModel
          };
          
          setMessages(prev => [...prev, errorMessage]);
          setCurrentResponse('');
          setIsLoading(false);
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsLoading(false);
      setCurrentResponse('');
    }
  }, [selectedModel, activeConversationId]);

  // Create new conversation
  const createConversation = useCallback(async (title: string) => {
    try {
      const newConv = await chatAPI.createConversation(title);
      setConversations(prev => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]); // Clear messages for new conversation
      return newConv;
    } catch (error) {
      console.error('Failed to create conversation:', error);
      return null;
    }
  }, []);

  return {
    messages,
    isLoading,
    currentResponse,
    availableModels,
    selectedModel,
    setSelectedModel,
    conversations,
    activeConversationId,
    setActiveConversationId,
    sendMessage,
    createConversation,
    loadConversations
  };
};

// Hook for external API data
export const useExternalData = () => {
  const [searchResults, setSearchResults] = useState<[]>([]);
  const [cryptoData, setCryptoData] = useState<unknown>(null);
  const [newsResults, setNewsResults] = useState<[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [apiHealth, setApiHealth] = useState<unknown>(null);

  // Search web
  const searchWeb = useCallback(async (query: string) => {
    setIsSearching(true);
    try {
      const data = await externalAPI.searchWeb(query);
      setSearchResults(data.results || []);
      return data;
    } catch (error) {
      console.error('Web search failed:', error);
      return null;
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Search news
  const searchNews = useCallback(async (query: string) => {
    setIsSearching(true);
    try {
      const data = await externalAPI.searchNews(query);
      setNewsResults(data.results || []);
      return data;
    } catch (error) {
      console.error('News search failed:', error);
      return null;
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Get crypto data
  const getCryptoData = useCallback(async () => {
    try {
      const data = await externalAPI.getCryptoMarket();
      setCryptoData(data.data);
      return data;
    } catch (error) {
      console.error('Crypto data fetch failed:', error);
      return null;
    }
  }, []);

  // Check API health
  const checkApiHealth = useCallback(async () => {
    try {
      const health = await externalAPI.getApiHealth();
      setApiHealth(health);
      return health;
    } catch (error) {
      console.error('API health check failed:', error);
      return null;
    }
  }, []);

  // Load API health on mount
  useEffect(() => {
    checkApiHealth();
  }, [checkApiHealth]);

  return {
    searchResults,
    cryptoData,
    newsResults,
    isSearching,
    apiHealth,
    searchWeb,
    searchNews,
    getCryptoData,
    checkApiHealth
  };
};

interface WebSocketMessage {
  type: string;
  content: string;
  timestamp?: string;
  [key: string]: unknown;
}

// Hook for WebSocket connection
export const useWebSocket = (conversationId: string | null) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!conversationId) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/chat/ws/${conversationId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages(prev => [...prev, data]);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setSocket(ws);
  }, [conversationId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socket) {
      socket.close();
      setSocket(null);
    }
    setIsConnected(false);
  }, [socket]);

  const sendMessage = useCallback((message: unknown) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    }
  }, [socket, isConnected]);

  useEffect(() => {
    if (conversationId) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [conversationId, connect, disconnect]);

  return {
    isConnected,
    messages,
    sendMessage,
    connect,
    disconnect
  };
};

// Hook for app capabilities
export const useAppCapabilities = () => {
  const [capabilities, setCapabilities] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadCapabilities = async () => {
      try {
        const data = await chatAPI.getChatCapabilities();
        setCapabilities(data);
      } catch (error) {
        console.error('Failed to load capabilities:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadCapabilities();
  }, []);

  return {
    capabilities,
    isLoading
  };
};