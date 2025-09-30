'use client';

import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MessageRendererProps, HeadingProps, ParagraphProps, ListProps, ListItemProps, BlockquoteProps, LinkProps } from '@/types/markdown';
import { DEFAULT_MARKDOWN_THEME } from '@/constants/markdown';
import { analyzeMarkdownFeatures, safeParseMarkdown } from '@/lib/markdown-utils';
import { MarkdownErrorBoundary } from './MarkdownErrorBoundary';
import { CodeBlock } from './CodeBlock';
import { useMarkdownTheme } from '@/hooks/useMarkdownTheme';

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

// Custom blockquote component
const CustomBlockquote: React.FC<BlockquoteProps> = ({ children, className }) => {
  return (
    <blockquote className={`${DEFAULT_MARKDOWN_THEME.typography.blockquote} ${className || ''}`}>
      {children}
    </blockquote>
  );
};

// Custom link component with security considerations
const CustomLink: React.FC<LinkProps> = ({ href, children, className }) => {
  const linkClass = `${DEFAULT_MARKDOWN_THEME.colors.linkColor} hover:${DEFAULT_MARKDOWN_THEME.colors.linkHover} underline transition-colors`;
  
  return (
    <a 
      href={href}
      className={`${linkClass} ${className || ''}`}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
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

// Custom table components
const CustomTable: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="overflow-x-auto mb-4">
      <table className="min-w-full border-collapse border border-gray-200 dark:border-gray-700">
        {children}
      </table>
    </div>
  );
};

const CustomTableHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <th className="border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-2 text-left font-semibold text-gray-900 dark:text-gray-100">
      {children}
    </th>
  );
};

const CustomTableCell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <td className="border border-gray-200 dark:border-gray-700 px-4 py-2 text-gray-700 dark:text-gray-300">
      {children}
    </td>
  );
};

export const MessageRenderer: React.FC<MessageRendererProps> = ({ 
  content, 
  isStreaming = false, 
  onCopyCode,
  className = '' 
}) => {
  // Use theme hook for consistent theming
  const { theme, isDarkMode } = useMarkdownTheme();

  // Analyze content features and safely parse markdown
  const { parsedContent, features, errors } = useMemo(() => {
    const { content: safeContent, errors: parseErrors } = safeParseMarkdown(content);
    const contentFeatures = analyzeMarkdownFeatures(safeContent);
    
    return {
      parsedContent: safeContent,
      features: contentFeatures,
      errors: parseErrors
    };
  }, [content]);

  // Custom components for react-markdown
  const components = useMemo(() => ({
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
    
    // Code handling with CodeBlock component
    code: ({ inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : undefined;
      
      return (
        <CodeBlock
          inline={inline}
          language={language}
          onCopy={onCopyCode}
          {...props}
        >
          {children}
        </CodeBlock>
      );
    },
    
    // Tables
    table: ({ children, ...props }: any) => <CustomTable {...props}>{children}</CustomTable>,
    th: ({ children, ...props }: any) => <CustomTableHeader {...props}>{children}</CustomTableHeader>,
    td: ({ children, ...props }: any) => <CustomTableCell {...props}>{children}</CustomTableCell>,
  }), []);

  // Handle error callback
  const handleError = (error: any) => {
    console.error('MessageRenderer error:', error);
  };

  return (
    <MarkdownErrorBoundary fallbackContent={content} onError={handleError}>
      <div className={`message-renderer ${className}`}>
        {/* Show streaming indicator if content is being streamed */}
        {isStreaming && (
          <div className="streaming-indicator mb-2">
            <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>Generating response...</span>
            </div>
          </div>
        )}
        
        {/* Render markdown content */}
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={components}
          className="markdown-content"
        >
          {parsedContent}
        </ReactMarkdown>
        
        {/* Show parsing errors in development */}
        {process.env.NODE_ENV === 'development' && errors.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
            <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Parsing Warnings:
            </div>
            <ul className="mt-1 text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside">
              {errors.map((error, index) => (
                <li key={index}>{error.message}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </MarkdownErrorBoundary>
  );
};

export default MessageRenderer;