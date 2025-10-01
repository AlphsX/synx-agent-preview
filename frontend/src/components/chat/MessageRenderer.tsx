'use client';

import React, { useMemo, useCallback, memo, lazy, Suspense } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MessageRendererProps, HeadingProps, ParagraphProps, ListProps, ListItemProps, BlockquoteProps, LinkProps } from '@/types/markdown';
import { DEFAULT_MARKDOWN_THEME } from '@/constants/markdown';
import { analyzeMarkdownFeatures, safeParseMarkdown } from '@/lib/markdown-utils';
import { MarkdownErrorBoundary } from './MarkdownErrorBoundary';
import { CodeBlock } from './CodeBlock';
import { useMarkdownTheme } from '@/hooks/useMarkdownTheme';
import { useComponentPerformanceMonitoring } from '@/hooks/usePerformanceMonitoring';
import { JSX } from 'react/jsx-runtime';

// Lazy load heavy components for better performance
const LazyCodeBlock = lazy(() => import('./CodeBlock').then(module => ({ default: module.CodeBlock })));



// Custom heading component
const CustomHeading: React.FC<HeadingProps & { level: number }> = ({ level, children, className }) => {
  const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements;
  const headingClass = DEFAULT_MARKDOWN_THEME.typography.headings[`h${level}` as keyof typeof DEFAULT_MARKDOWN_THEME.typography.headings];
  
  return (
    <HeadingTag className={`${headingClass} ${className || ''}`}>
      {children}
    </HeadingTag>
  );
};

// Custom paragraph component
const CustomParagraph: React.FC<ParagraphProps> = ({ children, className }) => {
  return (
    <p className={`${DEFAULT_MARKDOWN_THEME.typography.paragraph} ${className || ''}`}>
      {children}
    </p>
  );
};

// Custom list components
const CustomList: React.FC<ListProps & { ordered?: boolean }> = ({ ordered, children, className }) => {
  const ListTag = ordered ? 'ol' : 'ul';
  const listClass = `${DEFAULT_MARKDOWN_THEME.typography.list} ${ordered ? 'list-decimal list-inside' : 'list-disc list-inside'}`;
  
  return (
    <ListTag className={`${listClass} ${className || ''}`}>
      {children}
    </ListTag>
  );
};

const CustomListItem: React.FC<ListItemProps> = ({ children, className }) => {
  return (
    <li className={`${DEFAULT_MARKDOWN_THEME.typography.listItem} ${className || ''}`}>
      {children}
    </li>
  );
};

// Enhanced blockquote component with better visual distinction
const CustomBlockquote: React.FC<BlockquoteProps> = ({ children, className }) => {
  return (
    <blockquote className={`
      border-l-4 border-blue-500 dark:border-blue-400 
      pl-6 py-4 mb-6 relative
      bg-gradient-to-r from-blue-50/50 to-transparent 
      dark:from-blue-900/20 dark:to-transparent
      rounded-r-lg
      before:content-['"'] before:absolute before:-left-2 before:-top-2 
      before:text-6xl before:text-blue-500/20 dark:before:text-blue-400/20
      before:font-serif before:leading-none
      ${className || ''}
    `}>
      <div className="relative z-10">
        {children}
      </div>
    </blockquote>
  );
};

// Enhanced link component with security considerations and better UX
const CustomLink: React.FC<LinkProps> = ({ href, children, className }) => {
  // Security: Validate and sanitize URLs
  const isValidUrl = (url: string): boolean => {
    try {
      const urlObj = new URL(url);
      return ['http:', 'https:', 'mailto:'].includes(urlObj.protocol);
    } catch {
      return false;
    }
  };

  // Don't render invalid or potentially dangerous URLs
  if (!href || !isValidUrl(href)) {
    return <span className="text-gray-500 dark:text-gray-400">[Invalid Link]</span>;
  }

  const isExternal = href.startsWith('http') && !href.includes(window.location.hostname);
  
  return (
    <a 
      href={href}
      className={`
        text-blue-600 dark:text-blue-400 
        hover:text-blue-800 dark:hover:text-blue-300
        underline decoration-blue-500/30 hover:decoration-blue-500/60
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2
        focus:ring-offset-white dark:focus:ring-offset-gray-900
        rounded-sm
        ${className || ''}
      `}
      target={isExternal ? "_blank" : undefined}
      rel={isExternal ? "noopener noreferrer" : undefined}
      title={isExternal ? `External link: ${href}` : href}
    >
      {children}
      {isExternal && (
        <svg 
          className="inline-block w-3 h-3 ml-1 opacity-60" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
          />
        </svg>
      )}
    </a>
  );
};

// Custom inline code component
const CustomInlineCode: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <code className={DEFAULT_MARKDOWN_THEME.typography.inlineCode}>
      {children}
    </code>
  );
};

// Enhanced table components with responsive design
const CustomTable: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="table-container overflow-x-auto mb-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <table className="min-w-full border-collapse bg-white dark:bg-gray-900/50">
        {children}
      </table>
    </div>
  );
};

const CustomTableHead: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <thead className="bg-gray-50 dark:bg-gray-800/50">
      {children}
    </thead>
  );
};

const CustomTableBody: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
      {children}
    </tbody>
  );
};

const CustomTableRow: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <tr className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors duration-150">
      {children}
    </tr>
  );
};

const CustomTableHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <th className="px-6 py-4 text-left font-semibold text-gray-900 dark:text-gray-100 text-sm tracking-wide uppercase border-b border-gray-200 dark:border-gray-700">
      {children}
    </th>
  );
};

const CustomTableCell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <td className="px-6 py-4 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
      {children}
    </td>
  );
};

export const MessageRenderer: React.FC<MessageRendererProps> = memo(({ 
  content, 
  isStreaming = false, 
  onCopyCode,
  className = '' 
}) => {
  // Enhanced performance monitoring
  const { startComponentRender, endComponentRender, recordComponentError } = useComponentPerformanceMonitoring('MessageRenderer');
  
  // Start performance monitoring
  React.useEffect(() => {
    startComponentRender();
  });

  // Use theme hook for consistent theming
  const { isDarkMode } = useMarkdownTheme();

  // Enhanced error handler with performance monitoring
  const handleError = useCallback((error: any) => {
    recordComponentError(error);
    
    // Report error to monitoring service in production
    if (process.env.NODE_ENV === 'production' && (window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: `MessageRenderer: ${error.message}`,
        fatal: false
      });
    }
  }, [recordComponentError]);

  // Memoized content parsing with enhanced error handling
  const { parsedContent, features, errors } = useMemo(() => {
    try {
      const { content: safeContent, errors: parseErrors } = safeParseMarkdown(content);
      const contentFeatures = analyzeMarkdownFeatures(safeContent);
      
      return {
        parsedContent: safeContent,
        features: contentFeatures,
        errors: parseErrors
      };
    } catch (error) {
      handleError(error);
      return {
        parsedContent: content || '',
        features: {
          hasHeaders: false,
          hasLists: false,
          hasTables: false,
          hasLinks: false,
          hasBlockquotes: false,
          estimatedReadTime: 0
        },
        errors: [{
          type: 'parsing' as const,
          message: 'Failed to parse markdown content',
          recoverable: true
        }]
      };
    }
  }, [content, handleError]);

  // Memoized copy handler
  const handleCopyCode = useCallback((code: string) => {
    if (onCopyCode) {
      onCopyCode(code);
    }
  }, [onCopyCode]);

  // Memoized custom components for react-markdown with performance optimizations
  const components = useMemo(() => {
    const memoizedComponents = {
    // Headings
    h1: ({ children, ...props }: any) => <CustomHeading level={1} {...props}>{children}</CustomHeading>,
    h2: ({ children, ...props }: any) => <CustomHeading level={2} {...props}>{children}</CustomHeading>,
    h3: ({ children, ...props }: any) => <CustomHeading level={3} {...props}>{children}</CustomHeading>,
    h4: ({ children, ...props }: any) => <CustomHeading level={4} {...props}>{children}</CustomHeading>,
    h5: ({ children, ...props }: any) => <CustomHeading level={5} {...props}>{children}</CustomHeading>,
    h6: ({ children, ...props }: any) => <CustomHeading level={6} {...props}>{children}</CustomHeading>,
    
    // Text elements
    p: ({ children, ...props }: any) => <CustomParagraph {...props}>{children}</CustomParagraph>,
    
    // Lists
    ul: ({ children, ...props }: any) => <CustomList ordered={false} {...props}>{children}</CustomList>,
    ol: ({ children, ...props }: any) => <CustomList ordered={true} {...props}>{children}</CustomList>,
    li: ({ children, ...props }: any) => <CustomListItem {...props}>{children}</CustomListItem>,
    
    // Blockquotes
    blockquote: ({ children, ...props }: any) => <CustomBlockquote {...props}>{children}</CustomBlockquote>,
    
    // Links
    a: ({ href, children, ...props }: any) => <CustomLink href={href} {...props}>{children}</CustomLink>,
    
    // Code handling with lazy-loaded CodeBlock component for better performance
    code: ({ inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : undefined;
      
      // Use lazy loading for code blocks to improve initial render performance
      if (!inline && language) {
        return (
          <Suspense fallback={
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
          }>
            <LazyCodeBlock
              inline={inline}
              language={language}
              onCopy={handleCopyCode}
              {...props}
            >
              {children}
            </LazyCodeBlock>
          </Suspense>
        );
      }
      
      // Use regular CodeBlock for inline code and simple blocks
      return (
        <CodeBlock
          inline={inline}
          language={language}
          onCopy={handleCopyCode}
          {...props}
        >
          {children}
        </CodeBlock>
      );
    },
    
    // Tables with enhanced structure
    table: ({ children, ...props }: any) => <CustomTable {...props}>{children}</CustomTable>,
    thead: ({ children, ...props }: any) => <CustomTableHead {...props}>{children}</CustomTableHead>,
    tbody: ({ children, ...props }: any) => <CustomTableBody {...props}>{children}</CustomTableBody>,
    tr: ({ children, ...props }: any) => <CustomTableRow {...props}>{children}</CustomTableRow>,
    th: ({ children, ...props }: any) => <CustomTableHeader {...props}>{children}</CustomTableHeader>,
    td: ({ children, ...props }: any) => <CustomTableCell {...props}>{children}</CustomTableCell>,
    };
    
    return memoizedComponents;
  }, [handleCopyCode]);

  // Enhanced performance monitoring and cleanup
  React.useEffect(() => {
    return () => {
      endComponentRender(content?.length || 0);
    };
  });

  return (
    <MarkdownErrorBoundary fallbackContent={content} onError={handleError}>
      <div className={`message-renderer ${className} ${isStreaming ? 'streaming' : ''}`}>
        {/* Show streaming indicator if content is being streamed */}
        {isStreaming && (
          <div className="streaming-indicator mb-2">
            <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex space-x-1">
                <div className="pulse-dot w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="pulse-dot w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="pulse-dot w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              </div>
              <span>Generating response...</span>
            </div>
          </div>
        )}
        
        {/* Render markdown content with error boundary */}
        <div className="markdown-content-wrapper">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={components}
            skipHtml={true} // Security: Skip HTML for safety
          >
            {parsedContent}
          </ReactMarkdown>
        </div>
        
        {/* Enhanced error display for development */}
        {process.env.NODE_ENV === 'development' && errors.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-center mb-2">
              <svg className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Parsing Warnings ({errors.length})
              </div>
            </div>
            <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
              {errors.map((error, index) => (
                <li key={index} className="flex items-start">
                  <span className="inline-block w-2 h-2 bg-yellow-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                  <span>
                    <strong>{error.type}:</strong> {error.message}
                    {'line' in error && error.line && <span className="text-xs ml-1">(line {error.line})</span>}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Performance metrics in development */}
        {process.env.NODE_ENV === 'development' && content && content.length > 1000 && (
          <div className="mt-2 text-xs text-gray-400 dark:text-gray-600">
            Content: {content.length} chars | Features: {Object.values(features).filter(Boolean).length}
          </div>
        )}
      </div>
    </MarkdownErrorBoundary>
  );
});

export default MessageRenderer;