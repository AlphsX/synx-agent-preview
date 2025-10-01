'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { SimpleMessageRenderer } from './SimpleMessageRenderer';

interface SimpleStreamingRendererProps {
  content: string;
  isComplete: boolean;
  onContentUpdate?: (content: string) => void;
}

export const SimpleStreamingRenderer: React.FC<SimpleStreamingRendererProps> = ({
  content,
  isComplete,
  onContentUpdate
}) => {
  const [displayContent, setDisplayContent] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Simple streaming effect - gradually reveal content
  useEffect(() => {
    if (!content) {
      setDisplayContent('');
      return;
    }

    setIsProcessing(true);
    
    // If content is complete, show it all at once
    if (isComplete) {
      setDisplayContent(content);
      setIsProcessing(false);
      onContentUpdate?.(content);
      return;
    }

    // For streaming, show content with a slight delay for smooth effect
    const timer = setTimeout(() => {
      setDisplayContent(content);
      setIsProcessing(false);
      onContentUpdate?.(content);
    }, 50);

    return () => clearTimeout(timer);
  }, [content, isComplete, onContentUpdate]);

  // Handle incomplete markdown gracefully
  const getSafeContent = useCallback((rawContent: string) => {
    if (!rawContent) return '';
    
    // If streaming and ends with incomplete code block, add temporary closing
    if (!isComplete && rawContent.includes('```')) {
      const codeBlockCount = (rawContent.match(/```/g) || []).length;
      if (codeBlockCount % 2 !== 0) {
        return rawContent + '\n```';
      }
    }
    
    return rawContent;
  }, [isComplete]);

  const safeContent = getSafeContent(displayContent);

  // Don't render anything if no content and complete
  if (!safeContent && isComplete) {
    return null;
  }

  return (
    <div className="simple-streaming-renderer">
      <SimpleMessageRenderer
        content={safeContent}
        isStreaming={!isComplete || isProcessing}
        onCopyCode={(code) => {
          navigator.clipboard.writeText(code);
        }}
      />
    </div>
  );
};

export default SimpleStreamingRenderer;