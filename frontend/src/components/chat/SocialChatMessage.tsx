"use client";

import React, { memo, useState } from "react";
import { MessageRenderer } from "./MessageRenderer";

interface SocialChatMessageProps {
  content: string;
  role: "user" | "assistant";
  timestamp?: Date;
  isStreaming?: boolean;
  onCopyCode?: (code: string) => void;
}

export const SocialChatMessage: React.FC<SocialChatMessageProps> = memo(
  ({ content, role, timestamp, isStreaming = false, onCopyCode }) => {
    const [showTime, setShowTime] = useState(false);

    const formatTime = (date: Date) => {
      return new Intl.DateTimeFormat("th-TH", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Bangkok",
      }).format(date);
    };

    return (
      <div
        className={`flex ${
          role === "user" ? "justify-end" : "justify-start"
        } mb-4 group`}
      >
        <div
          className={`flex items-end space-x-2 max-w-[85%] ${
            role === "user" ? "flex-row-reverse space-x-reverse" : ""
          }`}
        >
          {/* Avatar */}
          <div className="flex-shrink-0 mb-1">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg ring-2 ring-white/20 ${
                role === "user"
                  ? "bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 text-white"
                  : "bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-500 text-white"
              }`}
            >
              {role === "user" ? "👨‍💻" : "🤖"}
            </div>
          </div>

          {/* Message Bubble */}
          <div className="flex flex-col">
            <div
              className={`relative px-5 py-4 rounded-2xl shadow-xl transition-all duration-200 hover:shadow-2xl ${
                role === "user"
                  ? "bg-white dark:bg-gray-800/90 text-gray-900 dark:text-gray-100 border border-gray-200/50 dark:border-gray-700/50 rounded-br-md"
                  : "bg-white dark:bg-gray-800/90 text-gray-900 dark:text-gray-100 border border-gray-200/50 dark:border-gray-700/50 rounded-bl-md"
              }`}
              onClick={() => setShowTime(!showTime)}
            >
              {/* Streaming indicator */}
              {isStreaming && role === "assistant" && (
                <div className="flex items-center space-x-1 mb-2 opacity-70">
                  <div className="flex space-x-1">
                    <div
                      className="w-2 h-2 bg-current rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-current rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-current rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    ></div>
                  </div>
                  <span className="text-xs">Typing...</span>
                </div>
              )}

              {/* Message Content */}
              <div
                className={`prose prose-sm max-w-none ${
                  role === "user"
                    ? "prose-invert"
                    : "prose-gray dark:prose-invert"
                }`}
              >
                {role === "user" ? (
                  <div className="text-gray-800 dark:text-gray-200 font-medium leading-relaxed">
                    {content}
                  </div>
                ) : (
                  <MessageRenderer
                    content={content}
                    isStreaming={isStreaming}
                    onCopyCode={onCopyCode}
                    className={`social-message-content assistant-content`}
                  />
                )}
              </div>

              {/* Message tail */}
              <div
                className={`absolute bottom-0 w-3 h-3 ${
                  role === "user"
                    ? "right-0 translate-x-1 bg-gradient-to-r from-blue-500 to-blue-600 rounded-bl-full"
                    : "left-0 -translate-x-1 bg-white dark:bg-gray-800 border-l border-b border-gray-200 dark:border-gray-700 rounded-br-full"
                }`}
              ></div>
            </div>

            {/* Timestamp */}
            {showTime && timestamp && (
              <div
                className={`text-xs text-gray-500 dark:text-gray-400 mt-1 px-2 ${
                  role === "user" ? "text-right" : "text-left"
                }`}
              >
                {formatTime(timestamp)}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
);

SocialChatMessage.displayName = "SocialChatMessage";

export default SocialChatMessage;
