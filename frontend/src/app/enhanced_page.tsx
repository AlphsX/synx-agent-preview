'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, Globe, TrendingUp, User, Bot, Mic, Paperclip, Zap, Activity } from 'lucide-react';
import { useChat, useExternalData, useAppCapabilities } from '@/hooks';
import { AIModelDropdown } from '@/components/magicui/ai-model-dropdown';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  model?: string;
}

interface AIModel {
  id: string;
  name: string;
  provider: string;
  description: string;
  features?: string[];
  recommended?: boolean;
}

export default function EnhancedHome() {
  const {
    messages,
    isLoading,
    currentResponse,
    availableModels,
    selectedModel,
    setSelectedModel,
    sendMessage
  } = useChat();

  const {
    searchResults,
    cryptoData,
    isSearching,
    apiHealth,
    searchWeb,
    getCryptoData
  } = useExternalData();

  const { capabilities } = useAppCapabilities();

  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentResponse]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const message = inputText;
    setInputText('');
    await sendMessage(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as React.FormEvent);
    }
  };

  const handleQuickAction = async (action: 'web' | 'crypto') => {
    if (action === 'web') {
      setInputText('Search the web for latest AI developments');
    } else if (action === 'crypto') {
      setInputText('Get current cryptocurrency market data');
    }
    inputRef.current?.focus();
  };

  // Initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: '1',
        content: 'Hello! I\'m Checkmate Spec Preview, your AI assistant with enhanced capabilities. I can search the web, get crypto data, and provide intelligent responses. Try asking me about current events or market trends!',
        role: 'assistant',
        timestamp: new Date(),
        model: selectedModel
      };
      // We would normally use setMessages here, but to keep the hook pattern clean,
      // this would be handled by the chat initialization
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-purple-600">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Checkmate Spec Preview</h1>
                <p className="text-sm text-gray-400">Enhanced AI Assistant</p>
              </div>
            </div>
            
            {/* Model Selector & Status */}
            <div className="flex items-center space-x-4">
              {/* API Health Indicator */}
              {apiHealth && (
                <div className="flex items-center space-x-2">
                  <Activity className={`h-4 w-4 ${
                    apiHealth.brave_search && apiHealth.binance ? 'text-green-500' : 'text-yellow-500'
                  }`} />
                  <span className="text-xs text-gray-400">
                    {apiHealth.brave_search && apiHealth.binance ? 'All APIs' : 'Limited APIs'}
                  </span>
                </div>
              )}
              
              <AIModelDropdown 
                selectedModel={selectedModel}
                onModelSelect={setSelectedModel}
              />
            </div>
          </div>

          {/* Capabilities Banner */}
          {capabilities && (
            <div className="mt-3 flex flex-wrap gap-2">
              {capabilities.features?.slice(0, 4).map((feature: string, index: number) => (
                <span key={index} className="px-2 py-1 bg-blue-600/20 text-blue-300 text-xs rounded-full">
                  {feature}
                </span>
              ))}
            </div>
          )}
        </div>
      </header>

      {/* Chat Container */}
      <div className="mx-auto max-w-4xl px-4 py-6">
        {/* Messages */}
        <div className="space-y-6 pb-32">
          {/* Welcome Message */}
          {messages.length === 0 && (
            <div className="flex justify-start">
              <div className="flex space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 to-pink-600">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div className="rounded-2xl border border-gray-700 bg-gray-800 px-4 py-3 max-w-[80%]">
                  <p className="text-sm leading-relaxed">
                    Hello! I&apos;m Checkmate Spec Preview, your AI assistant with enhanced capabilities. 
                    I can search the web in real-time, get cryptocurrency market data, and provide 
                    intelligent responses with current information. What would you like to explore?
                  </p>
                  <div className="mt-2 text-xs text-gray-400">
                    Enhanced with {capabilities?.external_apis || 3} external APIs
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[80%] space-x-3 ${
                message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}>
                {/* Avatar */}
                <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
                  message.role === 'user' 
                    ? 'bg-blue-600' 
                    : 'bg-gradient-to-r from-purple-600 to-pink-600'
                }`}>
                  {message.role === 'user' ? (
                    <User className="h-4 w-4 text-white" />
                  ) : (
                    <Bot className="h-4 w-4 text-white" />
                  )}
                </div>
                
                {/* Message Content */}
                <div className={`rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100 border border-gray-700'
                }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  {message.role === 'assistant' && message.model && (
                    <div className="mt-2 text-xs text-gray-400 flex items-center gap-2">
                      <Zap className="h-3 w-3" />
                      {availableModels.find(m => m.id === message.model)?.name || message.model}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {/* Current Response (Streaming) */}
          {currentResponse && (
            <div className="flex justify-start">
              <div className="flex space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 to-pink-600">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div className="rounded-2xl border border-gray-700 bg-gray-800 px-4 py-3 max-w-[80%]">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{currentResponse}</p>
                  <div className="mt-2 text-xs text-gray-400 flex items-center gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    Streaming response...
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Loading indicator */}
          {isLoading && !currentResponse && (
            <div className="flex justify-start">
              <div className="flex space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-purple-600 to-pink-600">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div className="rounded-2xl border border-gray-700 bg-gray-800 px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 rounded-full bg-gray-500 animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 rounded-full bg-gray-500 animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 rounded-full bg-gray-500 animate-bounce"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-gray-700 bg-gray-900/95 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <form onSubmit={handleSubmit} className="flex items-end space-x-4">
            {/* Attachment button */}
            <button
              type="button"
              className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
            >
              <Paperclip className="h-5 w-5" />
            </button>
            
            {/* Text input */}
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything... I have real-time web search, crypto data, and more!"
                className="w-full resize-none rounded-2xl bg-gray-800 border border-gray-600 px-4 py-3 pr-20 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                rows={1}
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={isLoading}
              />
              
              {/* Quick action buttons */}
              <div className="absolute right-2 top-2 flex space-x-1">
                <button
                  type="button"
                  onClick={() => handleQuickAction('web')}
                  className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white transition-colors"
                  title="Search web"
                  disabled={isLoading}
                >
                  <Globe className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickAction('crypto')}
                  className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white transition-colors"
                  title="Get crypto data"
                  disabled={isLoading}
                >
                  <TrendingUp className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            {/* Voice input button */}
            <button
              type="button"
              className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
              disabled={isLoading}
            >
              <Mic className="h-5 w-5" />
            </button>
            
            {/* Send button */}
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-400 transition-colors"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
          
          {/* Footer info */}
          <div className="mt-2 text-center text-xs text-gray-500">
            Checkmate Spec Preview can make mistakes. Enhanced with real-time data capabilities.
          </div>
        </div>
      </div>
    </div>
  );
}