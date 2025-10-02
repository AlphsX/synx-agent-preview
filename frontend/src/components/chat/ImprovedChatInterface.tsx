'use client';

import React, { useState, useRef, useEffect } from 'react';
import { SimpleMessageRenderer } from './SimpleMessageRenderer';
import { SimpleStreamingRenderer } from './SimpleStreamingRenderer';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
  model?: string;
}

interface ImprovedChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  className?: string;
}

export const ImprovedChatInterface: React.FC<ImprovedChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading = false,
  className = ''
}) => {
  const [inputValue, setInputValue] = useState('');
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

  const handleSend = () => {
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 ? (
            /* Welcome Message */
            <div className="text-center py-16">
              <div className="w-20 h-20 bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl ring-4 ring-white/10">
                <span className="text-3xl">🤖</span>
              </div>
              <h3 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent mb-3">
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
                    className="flex justify-start"
                  >
                    <div className="flex max-w-[85%] space-x-3">
                      {/* Avatar */}
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20">
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
                  }`}
                >
                <div className="flex max-w-[85%] space-x-3">
                  
                  {/* Avatar */}
                  {message.role === "assistant" && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20">
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
                          <p className="mb-0 leading-relaxed text-gray-800 dark:text-gray-200 font-medium">{message.content}</p>
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
                    </div>
                  </div>

                  {/* User Avatar */}
                  {message.role === "user" && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20">
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
      <div className="flex-shrink-0 p-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-t border-gray-200 dark:border-gray-700">
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
                className="w-full px-4 py-3 pr-12 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px] max-h-32 transition-all duration-200"
                rows={1}
              />
            </div>

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-full flex items-center justify-center transition-all duration-300 disabled:cursor-not-allowed shadow-xl hover:shadow-2xl disabled:shadow-sm hover:scale-110 disabled:scale-100 ring-2 ring-white/20 hover:ring-white/30"
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

export default ImprovedChatInterface;