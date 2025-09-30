'use client';

import React from 'react';
import { User, Bot, Clock, Copy, Check, AlertCircle } from 'lucide-react';
import { StreamingRenderer } from '@/components/chat/StreamingRenderer';
import { CopyButton } from '@/components/ui/CopyButton';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  model?: string;
  isStreaming?: boolean;
}

export interface EnhancedMessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
  onCopyMessage?: (content: string) => void;
  className?: string;
}

export const EnhancedMessageBubble: React.FC<EnhancedMessageBubbleProps> = ({
  message,
  isStreaming = false,
  onCopyMessage,
  className = '',
}) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).format(timestamp);
  };

  const handleCopyMessage = () => {
    onCopyMessage?.(message.content);
  };

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} group ${className}`}
    >
      <div
        className={`
          relative max-w-[85%] sm:max-w-[75%] md:max-w-[65%] lg:max-w-[60%]
          ${isUser ? 'ml-auto' : 'mr-auto'}
        `}
      >
        {/* Message Container */}
        <div
          className={`
            relative rounded-2xl px-4 py-3 sm:px-6 sm:py-4 
            shadow-sm border transition-all duration-200 ease-in-out
            ${
              isUser
                ? `
                  bg-gradient-to-r from-blue-600 to-blue-700 
                  dark:from-blue-500 dark:to-blue-600 
                  text-white border-blue-500/20
                  hover:shadow-md hover:shadow-blue-500/25
                `
                : `
                  bg-white dark:bg-gray-800/60 
                  text-gray-900 dark:text-gray-100 
                  border-gray-200/40 dark:border-gray-700/40
                  hover:shadow-md hover:bg-gray-50/50 dark:hover:bg-gray-800/80
                `
            }
          `}
        >
          {/* Avatar and Role Indicator */}
          <div className="flex items-start gap-3">
            {/* Avatar */}
            <div
              className={`
                flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                ${
                  isUser
                    ? 'bg-white/20 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                }
              `}
            >
              {isUser ? (
                <User className="w-4 h-4" />
              ) : (
                <Bot className="w-4 h-4" />
              )}
            </div>

            {/* Content Area */}
            <div className="flex-1 min-w-0">
              {/* Role Label */}
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`
                    text-xs font-medium uppercase tracking-wide
                    ${
                      isUser
                        ? 'text-white/80'
                        : 'text-gray-500 dark:text-gray-400'
                    }
                  `}
                >
                  {isUser ? 'You' : 'Assistant'}
                </span>
                
                {/* Copy Button */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <CopyButton
                    text={message.content}
                    size="sm"
                    variant="ghost"
                    onCopy={handleCopyMessage}
                    className={`
                      ${
                        isUser
                          ? 'text-white/70 hover:text-white hover:bg-white/10'
                          : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                      }
                    `}
                    aria-label="Copy message"
                  />
                </div>
              </div>

              {/* Message Content */}
              <div
                className={`
                  prose prose-sm max-w-none
                  ${
                    isUser
                      ? `
                        prose-invert
                        prose-p:text-white prose-p:leading-relaxed
                        prose-strong:text-white prose-em:text-white
                        prose-code:text-white prose-code:bg-white/20
                        prose-pre:bg-white/10 prose-pre:border-white/20
                      `
                      : `
                        prose-gray dark:prose-invert
                        prose-p:text-gray-900 dark:prose-p:text-gray-100
                        prose-p:leading-relaxed
                        prose-headings:text-gray-900 dark:prose-headings:text-gray-100
                        prose-strong:text-gray-900 dark:prose-strong:text-gray-100
                        prose-code:text-gray-800 dark:prose-code:text-gray-200
                        prose-code:bg-gray-100 dark:prose-code:bg-gray-700
                        prose-pre:bg-gray-50 dark:prose-pre:bg-gray-800
                        prose-pre:border-gray-200 dark:prose-pre:border-gray-700
                        prose-blockquote:border-gray-300 dark:prose-blockquote:border-gray-600
                        prose-blockquote:text-gray-700 dark:prose-blockquote:text-gray-300
                        prose-a:text-blue-600 dark:prose-a:text-blue-400
                        prose-a:hover:text-blue-700 dark:prose-a:hover:text-blue-300
                      `
                  }
                `}
              >
                {isAssistant ? (
                  <StreamingRenderer
                    content={message.content}
                    isComplete={!isStreaming}
                  />
                ) : (
                  <p className="mb-0 whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                )}
              </div>

              {/* Loading Indicator for Streaming */}
              {isStreaming && isAssistant && (
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse delay-75"></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse delay-150"></div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Thinking...
                  </span>
                </div>
              )}

              {/* Metadata Footer */}
              <div
                className={`
                  flex items-center justify-between mt-3 pt-3 
                  border-t border-opacity-20
                  ${
                    isUser
                      ? 'border-white/20'
                      : 'border-gray-200 dark:border-gray-700/50'
                  }
                `}
              >
                {/* Timestamp */}
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3 opacity-60" />
                  <span
                    className={`
                      text-xs opacity-75
                      ${
                        isUser
                          ? 'text-white/70'
                          : 'text-gray-500 dark:text-gray-400'
                      }
                    `}
                  >
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>

                {/* Model Info for Assistant */}
                {isAssistant && message.model && (
                  <div className="flex items-center gap-1">
                    <span
                      className={`
                        text-xs font-medium px-2 py-1 rounded-full
                        bg-gray-100 dark:bg-gray-700 
                        text-gray-600 dark:text-gray-300
                      `}
                    >
                      {message.model}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Message Status Indicators */}
        {isUser && (
          <div className="flex justify-end mt-1">
            <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <Check className="w-3 h-3" />
              <span>Sent</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedMessageBubble;