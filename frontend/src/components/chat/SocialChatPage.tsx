'use client';

import React, { useState, useCallback } from 'react';
import { SocialChatInterface } from './SocialChatInterface';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
}

export const SocialChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Mock API call - replace with your actual API
  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      role: 'user',
      timestamp: new Date()
    };

    // Add user message
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock response - replace with actual API call
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        content: `Thank you for your question: "${content}"\n\nThis is an example response with **markdown formatting** and emoji! 😊\n\n### Example Code Block:\n\`\`\`javascript\nconst greeting = "Hello!";\nconsole.log(greeting);\n\`\`\`\n\nHope this helps! Do you have any other questions? 🤔`,
        role: 'assistant',
        timestamp: new Date(),
        isStreaming: false
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: 'Sorry, there was an error sending the message. Please try again 😅',
        role: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="h-screen">
      <SocialChatInterface
        messages={messages}
        onSendMessage={sendMessage}
        isLoading={isLoading}
      />
    </div>
  );
};

export default SocialChatPage;