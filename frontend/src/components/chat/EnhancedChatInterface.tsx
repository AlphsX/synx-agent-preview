'use client';

import React, { useState, useRef, useEffect } from 'react';
import { SimpleMessageRenderer } from './SimpleMessageRenderer';
import { SimpleStreamingRenderer } from './SimpleStreamingRenderer';
import { FallbackResponseGenerator } from '@/lib/fallback-responses';
import { analyzeMarkdownFeatures } from '@/lib/markdown-utils';
import { chatAPI } from '@/lib/api';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
  model?: string;
  formattingMetadata?: {
    hasHeaders: boolean;
    hasLists: boolean;
    hasTables: boolean;
    hasLinks: boolean;
    hasBlockquotes: boolean;
    estimatedReadTime: number;
  };
}

interface EnhancedChatInterfaceProps {
  selectedModel: string;
  className?: string;
}

export const EnhancedChatInterface: React.FC<EnhancedChatInterfaceProps> = ({
  selectedModel,
  className = ''
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const messageContent = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: messageContent,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    // Add AI message placeholder
    const aiMessageId = `ai-${Date.now()}`;
    const aiMessage: Message = {
      id: aiMessageId,
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      model: selectedModel,
      isStreaming: true,
      formattingMetadata: {
        hasHeaders: false,
        hasLists: false,
        hasTables: false,
        hasLinks: false,
        hasBlockquotes: false,
        estimatedReadTime: 0
      },
    };

    setMessages(prev => [...prev, aiMessage]);

    try {
      const conversationId = "default-conversation";

      await chatAPI.streamChat(
        conversationId,
        messageContent,
        selectedModel,
        // onChunk
        (chunk: string) => {
          setMessages(prev =>
            prev.map(msg => {
              if (msg.id === aiMessageId) {
                const updatedContent = msg.content + chunk;
                const updatedFeatures = analyzeMarkdownFeatures(updatedContent);
                return { 
                  ...msg, 
                  content: updatedContent, 
                  isStreaming: true,
                  formattingMetadata: {
                    hasHeaders: updatedFeatures.hasHeaders,
                    hasLists: updatedFeatures.hasLists,
                    hasTables: updatedFeatures.hasTables,
                    hasLinks: updatedFeatures.hasLinks,
                    hasBlockquotes: updatedFeatures.hasBlockquotes,
                    estimatedReadTime: updatedFeatures.estimatedReadTime
                  }
                };
              }
              return msg;
            })
          );
        },
        // onComplete
        (data: unknown) => {
          console.log("Enhanced chat stream completed:", data);
          setMessages(prev =>
            prev.map(msg => {
              if (msg.id === aiMessageId) {
                const finalFeatures = analyzeMarkdownFeatures(msg.content);
                return { 
                  ...msg, 
                  isStreaming: false,
                  formattingMetadata: {
                    hasHeaders: finalFeatures.hasHeaders,
                    hasLists: finalFeatures.hasLists,
                    hasTables: finalFeatures.hasTables,
                    hasLinks: finalFeatures.hasLinks,
                    hasBlockquotes: finalFeatures.hasBlockquotes,
                    estimatedReadTime: finalFeatures.estimatedReadTime
                  }
                };
              }
              return msg;
            })
          );
          setIsLoading(false);
        },
        // onError - Enhanced error handling
        (error: string) => {
          console.error("Enhanced chat stream error:", error);
          
          // Generate intelligent fallback response
          const fallbackResponse = FallbackResponseGenerator.generateResponse(messageContent, error);
          
          let friendlyError = "Sorry, there was an error processing the data 😅 Let me try to help you in another way! 💫\n\n";
          friendlyError += fallbackResponse.content;
          
          // Add suggestions if available
          if (fallbackResponse.suggestions && fallbackResponse.suggestions.length > 0) {
            friendlyError += "\n\n## 💡 Suggested Questions:\n";
            fallbackResponse.suggestions.forEach((suggestion, index) => {
              friendlyError += `${index + 1}. ${suggestion}\n`;
            });
          }
          
          friendlyError += `\n\n${FallbackResponseGenerator.getRandomEncouragement()}`;
          
          setMessages(prev =>
            prev.map(msg => {
              if (msg.id === aiMessageId) {
                const errorFeatures = analyzeMarkdownFeatures(friendlyError);
                return {
                  ...msg,
                  content: friendlyError,
                  isStreaming: false,
                  formattingMetadata: {
                    hasHeaders: errorFeatures.hasHeaders,
                    hasLists: errorFeatures.hasLists,
                    hasTables: errorFeatures.hasTables,
                    hasLinks: errorFeatures.hasLinks,
                    hasBlockquotes: errorFeatures.hasBlockquotes,
                    estimatedReadTime: errorFeatures.estimatedReadTime
                  },
                };
              }
              return msg;
            })
          );
          setIsLoading(false);
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`flex flex-col h-full bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 dark:from-gray-900 dark:via-slate-900 dark:to-indigo-950/30 ${className}`}>
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 enhanced-scrollbar">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 ? (
            /* Welcome Message */
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl ring-4 ring-white/10 animate-pulse">
                <span className="text-4xl">🤖</span>
              </div>
              <h3 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent mb-4">
                Hello! Welcome
              </h3>
              <p className="text-gray-600 dark:text-gray-300 max-w-lg mx-auto text-lg leading-relaxed">
                I'm ready to help answer your questions and chat with you. How can I assist you today? 😊
              </p>
            </div>
          ) : (
            /* Chat Messages */
            messages.map((message) => {
              // Don't render assistant messages with no content unless they're streaming
              if (message.role === "assistant" && !message.content && !message.isStreaming) {
                return null;
              }

              // For assistant messages that are streaming but have no content, show just the loading indicator
              if (message.role === "assistant" && !message.content && message.isStreaming) {
                return (
                  <div
                    key={message.id}
                    className="flex justify-start message-enter"
                  >
                    <div className="flex max-w-[85%] space-x-3">
                      {/* Avatar */}
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20 avatar-glow">
                          <span className="text-lg">🤖</span>
                        </div>
                      </div>

                      {/* Loading indicator only */}
                      <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 py-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                        <span>Thinking...</span>
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  } message-enter`}
                >
                  <div className="flex max-w-[85%] space-x-3">
                    
                    {/* Avatar */}
                    {message.role === "assistant" && (
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20 avatar-glow">
                          <span className="text-lg">🤖</span>
                        </div>
                      </div>
                    )}

                    {/* Message Content */}
                    <div className="flex-1">
                      <div
                        className={`rounded-2xl px-5 py-4 shadow-lg border transition-all duration-200 hover:shadow-xl ${
                          message.role === "user"
                            ? "bg-white dark:bg-gray-800/90 text-gray-900 dark:text-gray-100 border-gray-200/50 dark:border-gray-700/50 rounded-br-md ml-auto"
                            : "bg-white dark:bg-gray-800/90 text-gray-900 dark:text-gray-100 border-gray-200/50 dark:border-gray-700/50 rounded-bl-md"
                        }`}
                      >
                        {message.role === "assistant" ? (
                          <SimpleStreamingRenderer
                            content={message.content}
                            isComplete={!message.isStreaming}
                            onContentUpdate={(renderedContent) => {
                              console.log("Content updated:", renderedContent);
                            }}
                          />
                        ) : (
                          <div className="prose prose-sm max-w-none prose-gray dark:prose-invert">
                            <p className="mb-0 leading-relaxed text-gray-800 dark:text-gray-200">
                              {message.content}
                            </p>
                          </div>
                        )}
                      
                      {/* Model info for assistant messages */}
                      {message.role === "assistant" && message.model && (
                        <div className="mt-3 pt-3 border-t border-gray-200/30 dark:border-gray-700/30">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                              {message.model}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {message.timestamp.toLocaleTimeString('th-TH', {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {/* User message timestamp */}
                      {message.role === "user" && (
                        <div className="mt-2 text-right">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {message.timestamp.toLocaleTimeString('th-TH', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* User Avatar */}
                  {message.role === "user" && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20 avatar-glow">
                        <span className="text-lg">👨‍💻</span>
                      </div>
                    </div>
                  )}
                    </div>

                    {/* User Avatar */}
                    {message.role === "user" && (
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20 avatar-glow">
                          <span className="text-lg">👨‍💻</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 px-4 py-5 glass-effect border-t border-gray-200/50 dark:border-gray-700/50 shadow-lg">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end space-x-3">
            
            {/* Message Input */}
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message here..."
                disabled={isLoading}
                className="w-full px-5 py-4 pr-12 bg-gray-50 dark:bg-gray-700/80 border border-gray-200 dark:border-gray-600 rounded-2xl resize-none focus-ring disabled:opacity-50 disabled:cursor-not-allowed min-h-[52px] max-h-32 shadow-sm hover:shadow-md transition-all duration-200 backdrop-blur-sm"
                rows={1}
              />
            </div>

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="send-button-enhanced flex-shrink-0 w-12 h-12 text-white rounded-full flex items-center justify-center transition-all duration-300 disabled:cursor-not-allowed shadow-xl hover:shadow-2xl disabled:shadow-sm hover:scale-110 disabled:scale-100 ring-2 ring-white/20 hover:ring-white/30"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedChatInterface;