'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { MarkdownError } from '@/types/markdown';

interface Props {
  children: ReactNode;
  fallbackContent?: string;
  onError?: (error: MarkdownError) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class MarkdownErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error and update state with error info
    this.setState({ errorInfo });

    // Create a structured markdown error
    const markdownError: MarkdownError = {
      type: 'rendering',
      message: error.message,
      recoverable: true
    };

    // Call the error callback if provided
    if (this.props.onError) {
      this.props.onError(markdownError);
    }

    // Log error for debugging
    console.error('Markdown rendering error:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI when markdown rendering fails
      return (
        <div className="markdown-error-boundary p-4 border border-red-200 rounded-lg bg-red-50 dark:bg-red-900/20 dark:border-red-800">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg 
                className="h-5 w-5 text-red-400" 
                viewBox="0 0 20 20" 
                fill="currentColor"
              >
                <path 
                  fillRule="evenodd" 
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" 
                  clipRule="evenodd" 
                />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Content Rendering Error
              </h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                There was an issue rendering the formatted content. The raw content is displayed below.
              </p>
              <div className="mt-3">
                <button
                  onClick={this.handleRetry}
                  className="text-sm bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:hover:bg-red-700 text-red-800 dark:text-red-200 px-3 py-1 rounded transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
          
          {/* Fallback content display */}
          <div className="mt-4 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded">
            <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
              {this.props.fallbackContent || 'Content could not be displayed'}
            </pre>
          </div>

          {/* Development error details */}
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="mt-4">
              <summary className="text-sm text-red-600 dark:text-red-400 cursor-pointer hover:text-red-800 dark:hover:text-red-200">
                Error Details (Development)
              </summary>
              <div className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-xs">
                <div className="font-semibold text-red-700 dark:text-red-300">Error:</div>
                <pre className="mt-1 text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {this.state.error.message}
                </pre>
                {this.state.errorInfo && (
                  <>
                    <div className="mt-3 font-semibold text-red-700 dark:text-red-300">Stack Trace:</div>
                    <pre className="mt-1 text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </>
                )}
              </div>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default MarkdownErrorBoundary;