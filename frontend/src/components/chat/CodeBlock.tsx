'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CodeBlockProps } from '@/types/markdown';
import { detectLanguage } from '@/lib/markdown-utils';
import { DEFAULT_MARKDOWN_THEME } from '@/constants/markdown';
import { useSyntaxHighlightingTheme } from '@/hooks/useMarkdownTheme';

// Copy button component
interface CopyButtonProps {
  onCopy: () => void;
  copied: boolean;
  disabled?: boolean;
}

const CopyButton: React.FC<CopyButtonProps> = ({ onCopy, copied, disabled = false }) => {
  return (
    <button
      onClick={onCopy}
      disabled={disabled}
      className={`
        absolute top-2 right-2 p-2 rounded-md transition-all duration-200
        ${copied 
          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' 
          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
      `}
      aria-label={copied ? 'Copied to clipboard' : 'Copy code to clipboard'}
      title={copied ? 'Copied!' : 'Copy code'}
    >
      {copied ? (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
};

// Language badge component
interface LanguageBadgeProps {
  language: string;
}

const LanguageBadge: React.FC<LanguageBadgeProps> = ({ language }) => {
  if (!language || language === 'plaintext' || language === 'text') {
    return null;
  }

  return (
    <div className="absolute top-2 left-3 px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs font-mono rounded">
      {language}
    </div>
  );
};

export const CodeBlock: React.FC<CodeBlockProps> = ({
  children,
  language,
  inline = false,
  showCopyButton = true,
  onCopy
}) => {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);

  // Detect language if not provided
  const detectedLanguage = useMemo(() => {
    return language ? detectLanguage(language) : 'plaintext';
  }, [language]);

  // Get the code content as string
  const codeContent = useMemo(() => {
    return String(children).replace(/\n$/, '');
  }, [children]);

  // Handle copy to clipboard
  const handleCopy = useCallback(async () => {
    try {
      setCopyError(false);
      
      // Try using the modern Clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(codeContent);
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement('textarea');
        textArea.value = codeContent;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (!successful) {
          throw new Error('Copy command failed');
        }
      }

      setCopied(true);
      
      // Call the onCopy callback if provided
      if (onCopy) {
        onCopy(codeContent);
      }

      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000);
      
    } catch (error) {
      console.error('Failed to copy code:', error);
      setCopyError(true);
      setTimeout(() => setCopyError(false), 2000);
    }
  }, [codeContent, onCopy]);

  // Use theme hook for consistent theming
  const { isDarkMode, backgroundColor, textColor, borderColor } = useSyntaxHighlightingTheme();
  const syntaxTheme = isDarkMode ? oneDark : oneLight;

  // Render inline code
  if (inline) {
    return (
      <code className={DEFAULT_MARKDOWN_THEME.typography.inlineCode}>
        {children}
      </code>
    );
  }

  // Render block code with syntax highlighting
  return (
    <div className="relative group">
      <div className={`
        ${DEFAULT_MARKDOWN_THEME.typography.code}
        relative overflow-hidden
        border border-gray-200 dark:border-gray-700
        rounded-lg
      `}>
        {/* Language badge */}
        <LanguageBadge language={detectedLanguage} />
        
        {/* Copy button */}
        {showCopyButton && (
          <CopyButton 
            onCopy={handleCopy} 
            copied={copied}
            disabled={copyError}
          />
        )}
        
        {/* Syntax highlighted code */}
        <SyntaxHighlighter
          language={detectedLanguage}
          style={syntaxTheme}
          customStyle={{
            margin: 0,
            padding: '1rem',
            paddingTop: detectedLanguage !== 'plaintext' ? '2.5rem' : '1rem',
            background: 'transparent',
            fontSize: '0.875rem',
            lineHeight: '1.5'
          }}
          codeTagProps={{
            style: {
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace'
            }
          }}
          showLineNumbers={codeContent.split('\n').length > 10}
          lineNumberStyle={{
            minWidth: '3em',
            paddingRight: '1em',
            color: isDarkMode ? '#6b7280' : '#9ca3af',
            borderRight: `1px solid ${isDarkMode ? '#374151' : '#e5e7eb'}`,
            marginRight: '1em'
          }}
          wrapLines={true}
          wrapLongLines={true}
        >
          {codeContent}
        </SyntaxHighlighter>
        
        {/* Copy error message */}
        {copyError && (
          <div className="absolute bottom-2 right-2 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs rounded">
            Copy failed
          </div>
        )}
      </div>
      
      {/* Mobile-friendly copy button for touch devices */}
      {showCopyButton && (
        <button
          onClick={handleCopy}
          className={`
            md:hidden absolute -bottom-10 right-0 px-3 py-1 text-sm rounded
            ${copied 
              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' 
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
            }
            transition-all duration-200
          `}
          disabled={copyError}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      )}
    </div>
  );
};

export default CodeBlock;