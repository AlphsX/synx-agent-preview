"use client";

import React, { memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface SimpleMessageRendererProps {
  content: string;
  isStreaming?: boolean;
  className?: string;
  onCopyCode?: (code: string) => void;
}

// Simple, robust code block component
const SimpleCodeBlock: React.FC<{
  children: string;
  className?: string;
  inline?: boolean;
}> = ({ children, className, inline }) => {
  const language = className?.replace("language-", "") || "text";

  if (inline) {
    return (
      <code className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono text-pink-600 dark:text-pink-400">
        {children}
      </code>
    );
  }

  return (
    <div className="my-4 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">
          {language}
        </span>
        <button
          onClick={() => navigator.clipboard.writeText(children)}
          className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded transition-colors"
        >
          Copy
        </button>
      </div>
      <pre className="p-4 overflow-x-auto">
        <code className="text-sm font-mono text-gray-800 dark:text-gray-200">
          {children}
        </code>
      </pre>
    </div>
  );
};

export const SimpleMessageRenderer: React.FC<SimpleMessageRendererProps> = memo(
  ({ content, isStreaming = false, className = "", onCopyCode }) => {
    // Simple markdown components with Thai-friendly styling
    const components = useMemo(
      () => ({
        // Headings with Thai typography
        h1: ({ children }: any) => (
          <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-gray-100 leading-relaxed">
            {children}
          </h1>
        ),
        h2: ({ children }: any) => (
          <h2 className="text-xl font-bold mb-3 text-gray-900 dark:text-gray-100 leading-relaxed">
            {children}
          </h2>
        ),
        h3: ({ children }: any) => (
          <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100 leading-relaxed">
            {children}
          </h3>
        ),

        // Paragraphs with better Thai line height
        p: ({ children }: any) => (
          <p className="mb-3 text-gray-800 dark:text-gray-200 leading-relaxed">
            {children}
          </p>
        ),

        // Lists
        ul: ({ children }: any) => (
          <ul className="mb-3 ml-4 space-y-1 list-disc text-gray-800 dark:text-gray-200">
            {children}
          </ul>
        ),
        ol: ({ children }: any) => (
          <ol className="mb-3 ml-4 space-y-1 list-decimal text-gray-800 dark:text-gray-200">
            {children}
          </ol>
        ),
        li: ({ children }: any) => (
          <li className="leading-relaxed">{children}</li>
        ),

        // Blockquotes
        blockquote: ({ children }: any) => (
          <blockquote className="border-l-4 border-blue-400 pl-4 py-2 mb-4 bg-blue-50 dark:bg-blue-900/20 rounded-r">
            <div className="text-gray-700 dark:text-gray-300 italic">
              {children}
            </div>
          </blockquote>
        ),

        // Links
        a: ({ href, children }: any) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline"
          >
            {children}
          </a>
        ),

        // Code blocks
        code: ({ inline, className, children }: any) => (
          <SimpleCodeBlock inline={inline} className={className}>
            {children}
          </SimpleCodeBlock>
        ),

        // Tables
        table: ({ children }: any) => (
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full border border-gray-200 dark:border-gray-700 rounded-lg">
              {children}
            </table>
          </div>
        ),
        th: ({ children }: any) => (
          <th className="px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 text-left font-semibold">
            {children}
          </th>
        ),
        td: ({ children }: any) => (
          <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            {children}
          </td>
        ),

        // Strong and emphasis
        strong: ({ children }: unknown) => (
          <strong className="font-bold text-gray-900 dark:text-gray-100">
            {children}
          </strong>
        ),
        em: ({ children }: unknown) => (
          <em className="italic text-gray-800 dark:text-gray-200">
            {children}
          </em>
        ),
      }),
      []
    );

    // Show only loading indicator when streaming with no content
    if (isStreaming && !content) {
      return (
        <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
          <span>Thinking...</span>
        </div>
      );
    }

    // Fallback for rendering errors
    if (!content) {
      return null; // Don't render anything if no content and not streaming
    }

    return (
      <div className={`simple-message-renderer ${className}`}>
        {/* Markdown content with error boundary */}
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={components}
            skipHtml={true}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    );
  }
);

SimpleMessageRenderer.displayName = "SimpleMessageRenderer";

export default SimpleMessageRenderer;
