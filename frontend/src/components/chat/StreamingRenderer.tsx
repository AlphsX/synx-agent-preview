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
    <div className="streaming-renderer-container relative">
      {/* Main content with enhanced animations */}
      <div className={`
        transition-all duration-300 ease-out
        ${streamingState.isProcessing ? 'animate-streaming-glow' : ''}
      `}>
        {renderedContent}
      </div>
      
      {/* Enhanced pending content indicator */}
      {showPendingIndicator && (
        <div className="pending-content-indicator mt-3 animate-fade-in-up">
          <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200/50 dark:border-blue-700/50 backdrop-blur-sm">
            <div className="flex items-center space-x-3">
              {/* Enhanced loading animation */}
              <div className="relative">
                <div className="w-4 h-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 w-4 h-4 border-2 border-transparent border-t-blue-400 rounded-full animate-spin animate-reverse" style={{ animationDelay: '0.5s' }}></div>
              </div>
              
              {/* Animated text with typing effect */}
              <div className="flex items-center space-x-1">
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                  Processing
                </span>
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
            
            {/* Progress indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-16 h-1 bg-blue-200/50 dark:bg-blue-800/50 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full animate-wave"></div>
              </div>
              <span className="text-xs text-blue-600/70 dark:text-blue-400/70 font-mono">
                {Math.round((streamingState.processedContent.length / (streamingState.processedContent.length + streamingState.pendingContent.length)) * 100)}%
              </span>
            </div>
          </div>
          
          {/* Development info with enhanced styling */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-2 p-2 bg-gray-100/50 dark:bg-gray-800/50 rounded border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm">
              <div className="text-xs font-mono text-gray-600 dark:text-gray-400 truncate">
                <span className="font-semibold">Pending:</span> {streamingState.pendingContent.substring(0, 50)}
                {streamingState.pendingContent.length > 50 && '...'}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Enhanced error display */}
      {process.env.NODE_ENV === 'development' && errors.length > 0 && (
        <div className="mt-3 animate-fade-in-up">
          <div className="p-4 bg-gradient-to-r from-red-50/80 to-pink-50/80 dark:from-red-900/20 dark:to-pink-900/20 border border-red-200/50 dark:border-red-700/50 rounded-lg backdrop-blur-sm">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <div className="text-sm font-semibold text-red-800 dark:text-red-200">
                Streaming Errors ({errors.length})
              </div>
            </div>
            
            <div className="space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
              {errors.map((error, index) => (
                <div key={index} className="flex items-start space-x-2 p-2 bg-white/50 dark:bg-gray-800/50 rounded border border-red-200/30 dark:border-red-700/30">
                  <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <div className="text-xs text-red-700 dark:text-red-300 font-mono">
                    <span className="font-semibold">[{error.type}]</span>{' '}
                    {'message' in error ? error.message : 'Unknown error'}
                    {'recovery' in error && (
                      <span className="text-red-600/70 dark:text-red-400/70">
                        {' '}(Recovery: {error.recovery})
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Streaming completion indicator */}
      {isComplete && streamingState.processedContent && (
        <div className="absolute -bottom-2 right-0 animate-fade-in">
          <div className="flex items-center space-x-1 px-2 py-1 bg-green-100/80 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-medium backdrop-blur-sm border border-green-200/50 dark:border-green-700/50">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
            <span>Complete</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StreamingRenderer;