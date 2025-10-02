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
        absolute top-2 right-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all
        ${copied 
          ? 'bg-green-500 text-white' 
          : 'bg-gray-700 dark:bg-gray-600 text-white hover:bg-gray-600 dark:hover:bg-gray-500'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      aria-label={copied ? 'Copied to clipboard' : 'Copy code to clipboard'}
      title={copied ? 'Copied!' : 'Copy code'}
    >
      {copied ? 'Copied!' : 'Copy'}
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
    <div className="absolute top-2 left-3 px-2 py-1 bg-blue-500 text-white text-xs font-medium rounded">
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
    <div className="my-4 relative group">
      <div className="relative overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
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
            lineHeight: '1.6'
          }}
          codeTagProps={{
            style: {
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace'
            }
          }}
          showLineNumbers={false}
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
    </div>
  );
};

export default CodeBlock;