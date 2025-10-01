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
        content: `ขอบคุณสำหรับคำถาม: "${content}"\n\nนี่คือตัวอย่างการตอบกลับที่มี **markdown formatting** และ emoji! 😊\n\n### ตัวอย่าง Code Block:\n\`\`\`javascript\nconst greeting = "สวัสดีครับ!";\nconsole.log(greeting);\n\`\`\`\n\nหวังว่าจะช่วยได้นะครับ! มีคำถามอื่นไหม? 🤔`,
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
        content: 'ขออภัยครับ เกิดข้อผิดพลาดในการส่งข้อความ กรุณาลองใหม่อีกครั้ง 😅',
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