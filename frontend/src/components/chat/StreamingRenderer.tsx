'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { StreamingRendererProps, StreamingState, StreamingError, MarkdownError } from '@/types/markdown';
import { MessageRenderer } from './MessageRenderer';
import { 
  validateMarkdownContent, 
  handleStreamingError, 
  debounce,
  safeParseMarkdown 
} from '@/lib/markdown-utils';

// Buffer management for streaming content
class StreamingBuffer {
  private buffer: string = '';
  private processedLength: number = 0;
  private pendingBlocks: string[] = [];
  
  append(chunk: string): void {
    this.buffer += chunk;
  }
  
  getProcessableContent(): { content: string; hasIncomplete: boolean } {
    // Find the last complete markdown block
    const lines = this.buffer.split('\n');
    const processableLines: string[] = [];
    let hasIncompleteCodeBlock = false;
    let inCodeBlock = false;
    let codeBlockCount = 0;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Track code block boundaries
      if (line.trim().startsWith('```')) {
        codeBlockCount++;
        inCodeBlock = codeBlockCount % 2 !== 0;
      }
      
      // If we're at the last line and in a code block, it might be incomplete
      if (i === lines.length - 1 && inCodeBlock) {
        hasIncompleteCodeBlock = true;
        break;
      }
      
      processableLines.push(line);
    }
    
    const processableContent = processableLines.join('\n');
    
    return {
      content: processableContent,
      hasIncomplete: hasIncompleteCodeBlock || inCodeBlock
    };
  }
  
  getFullContent(): string {
    return this.buffer;
  }
  
  clear(): void {
    this.buffer = '';
    this.processedLength = 0;
    this.pendingBlocks = [];
  }
  
  isEmpty(): boolean {
    return this.buffer.length === 0;
  }
}

// Error recovery strategies
const recoverFromStreamingError = (error: StreamingError): string => {
  switch (error.recovery) {
    case 'retry':
      // For retry, return the content as-is and let the next chunk fix it
      return error.content;
    case 'fallback':
      // For fallback, try to clean up the content
      return handleStreamingError(error);
    case 'skip':
      // For skip, remove the problematic content
      return error.content.substring(0, error.position);
    default:
      return error.content;
  }
};

// Detect streaming errors
const detectStreamingErrors = (content: string): StreamingError[] => {
  const errors: StreamingError[] = [];
  
  // Check for incomplete code blocks
  const codeBlockMatches = content.match(/```/g);
  if (codeBlockMatches && codeBlockMatches.length % 2 !== 0) {
    const lastCodeBlockIndex = content.lastIndexOf('```');
    errors.push({
      type: 'incomplete-markdown',
      content,
      position: lastCodeBlockIndex,
      recovery: 'retry'
    });
  }
  
  // Check for malformed code blocks (code block without language or content)
  const malformedCodeBlock = /```\s*$/.test(content);
  if (malformedCodeBlock) {
    errors.push({
      type: 'malformed-code-block',
      content,
      position: content.lastIndexOf('```'),
      recovery: 'fallback'
    });
  }
  
  return errors;
};

export const StreamingRenderer: React.FC<StreamingRendererProps> = ({
  content,
  isComplete,
  onContentUpdate
}) => {
  const [streamingState, setStreamingState] = useState<StreamingState>({
    processedContent: '',
    pendingContent: '',
    isProcessing: false
  });
  
  const [errors, setErrors] = useState<(MarkdownError | StreamingError)[]>([]);
  const bufferRef = useRef<StreamingBuffer>(new StreamingBuffer());
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Debounced content processing to avoid excessive re-renders
  const debouncedProcess = useCallback(
    debounce((content: string) => {
      processStreamingContent(content);
    }, 100),
    []
  );
  
  // Process streaming content with error recovery
  const processStreamingContent = useCallback((newContent: string) => {
    setStreamingState(prev => ({ ...prev, isProcessing: true }));
    
    try {
      bufferRef.current.append(newContent);
      
      const { content: processableContent, hasIncomplete } = bufferRef.current.getProcessableContent();
      const fullContent = bufferRef.current.getFullContent();
      
      // Detect streaming errors
      const streamingErrors = detectStreamingErrors(fullContent);
      
      // Validate markdown content
      const markdownErrors = validateMarkdownContent(processableContent);
      
      // Combine all errors
      const allErrors = [...streamingErrors, ...markdownErrors];
      setErrors(allErrors);
      
      // Apply error recovery if needed
      let finalContent = processableContent;
      if (streamingErrors.length > 0) {
        const lastError = streamingErrors[streamingErrors.length - 1];
        finalContent = recoverFromStreamingError(lastError);
      }
      
      // Update state
      setStreamingState({
        processedContent: finalContent,
        pendingContent: hasIncomplete ? fullContent.substring(finalContent.length) : '',
        isProcessing: false
      });
      
      // Notify parent component
      if (onContentUpdate) {
        onContentUpdate(finalContent);
      }
      
    } catch (error) {
      console.error('StreamingRenderer processing error:', error);
      setStreamingState(prev => ({
        ...prev,
        processedContent: bufferRef.current.getFullContent(),
        isProcessing: false
      }));
    }
  }, [onContentUpdate]);
  
  // Handle content updates
  useEffect(() => {
    if (content) {
      // Clear buffer if this is a new message
      if (content.length < bufferRef.current.getFullContent().length) {
        bufferRef.current.clear();
        setStreamingState({
          processedContent: '',
          pendingContent: '',
          isProcessing: false
        });
      }
      
      // Process new content
      const currentContent = bufferRef.current.getFullContent();
      const newChunk = content.substring(currentContent.length);
      
      if (newChunk) {
        debouncedProcess(newChunk);
      }
    }
  }, [content, debouncedProcess]);
  
  // Handle completion
  useEffect(() => {
    if (isComplete && bufferRef.current.getFullContent()) {
      // Clear any processing timeouts
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
      
      // Process final content
      const finalContent = bufferRef.current.getFullContent();
      const { content: safeContent } = safeParseMarkdown(finalContent);
      
      setStreamingState({
        processedContent: safeContent,
        pendingContent: '',
        isProcessing: false
      });
      
      if (onContentUpdate) {
        onContentUpdate(safeContent);
      }
    }
  }, [isComplete, onContentUpdate]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
    };
  }, []);
  
  // Memoize the rendered content to avoid unnecessary re-renders
  const renderedContent = useMemo(() => {
    const contentToRender = streamingState.processedContent || content;
    
    if (!contentToRender) {
      return null;
    }
    
    return (
      <MessageRenderer
        content={contentToRender}
        isStreaming={!isComplete || streamingState.isProcessing}
        className="streaming-renderer"
      />
    );
  }, [streamingState.processedContent, content, isComplete, streamingState.isProcessing]);
  
  // Show pending content indicator if there's incomplete content
  const showPendingIndicator = streamingState.pendingContent && !isComplete;
  
  return (
    <div className="streaming-renderer-container">
      {renderedContent}
      
      {/* Pending content indicator */}
      {showPendingIndicator && (
        <div className="pending-content-indicator mt-2 p-2 bg-gray-50 dark:bg-gray-800 rounded border-l-4 border-blue-500">
          <div className="flex items-center space-x-2">
            <div className="animate-spin w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="text-xs text-gray-600 dark:text-gray-400">
              Processing incomplete content...
            </span>
          </div>
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-1 text-xs font-mono text-gray-500 dark:text-gray-500 truncate">
              Pending: {streamingState.pendingContent.substring(0, 50)}...
            </div>
          )}
        </div>
      )}
      
      {/* Error display in development */}
      {process.env.NODE_ENV === 'development' && errors.length > 0 && (
        <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
          <div className="text-sm font-medium text-red-800 dark:text-red-200">
            Streaming Errors ({errors.length}):
          </div>
          <ul className="mt-1 text-xs text-red-700 dark:text-red-300 list-disc list-inside max-h-20 overflow-y-auto">
            {errors.map((error, index) => (
              <li key={index}>
                [{error.type}] {'message' in error ? error.message : 'Unknown error'}
                {'recovery' in error && ` (Recovery: ${error.recovery})`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default StreamingRenderer;