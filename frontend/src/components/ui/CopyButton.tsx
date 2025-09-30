'use client';

import React, { useState, useCallback } from 'react';
import { Check, Copy, AlertCircle } from 'lucide-react';

export interface CopyButtonProps {
  text: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'ghost' | 'outline';
  onCopy?: (text: string) => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
  'aria-label'?: string;
}

export type CopyState = 'idle' | 'copying' | 'success' | 'error';

export const CopyButton: React.FC<CopyButtonProps> = ({
  text,
  className = '',
  size = 'md',
  variant = 'default',
  onCopy,
  onError,
  disabled = false,
  'aria-label': ariaLabel = 'Copy to clipboard',
}) => {
  const [copyState, setCopyState] = useState<CopyState>('idle');

  const handleCopy = useCallback(async () => {
    if (disabled || copyState === 'copying') return;

    setCopyState('copying');

    try {
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement('textarea');
        textArea.value = text;
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

      setCopyState('success');
      onCopy?.(text);

      // Reset to idle after 2 seconds
      setTimeout(() => {
        setCopyState('idle');
      }, 2000);
    } catch (error) {
      setCopyState('error');
      const copyError = error instanceof Error ? error : new Error('Copy failed');
      onError?.(copyError);

      // Reset to idle after 3 seconds for error state
      setTimeout(() => {
        setCopyState('idle');
      }, 3000);
    }
  }, [text, disabled, copyState, onCopy, onError]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleCopy();
    }
  }, [handleCopy]);

  // Size classes
  const sizeClasses = {
    sm: 'h-6 w-6 p-1',
    md: 'h-8 w-8 p-1.5',
    lg: 'h-10 w-10 p-2',
  };

  // Variant classes
  const variantClasses = {
    default: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600',
    ghost: 'hover:bg-gray-100 dark:hover:bg-gray-700',
    outline: 'border border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700',
  };

  // State-specific classes
  const stateClasses = {
    idle: '',
    copying: 'opacity-75 cursor-wait',
    success: 'bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-700 dark:text-green-300',
    error: 'bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-700 dark:text-red-300',
  };

  const getIcon = () => {
    switch (copyState) {
      case 'copying':
        return <Copy className="animate-pulse" />;
      case 'success':
        return <Check className="animate-in fade-in duration-200" />;
      case 'error':
        return <AlertCircle className="animate-in fade-in duration-200" />;
      default:
        return <Copy />;
    }
  };

  const getAriaLabel = () => {
    switch (copyState) {
      case 'copying':
        return 'Copying to clipboard...';
      case 'success':
        return 'Copied to clipboard successfully';
      case 'error':
        return 'Failed to copy to clipboard';
      default:
        return ariaLabel;
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      onKeyDown={handleKeyDown}
      disabled={disabled || copyState === 'copying'}
      className={`
        inline-flex items-center justify-center
        rounded-md
        transition-all duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        dark:focus:ring-offset-gray-800
        disabled:opacity-50 disabled:cursor-not-allowed
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${stateClasses[copyState]}
        ${className}
      `}
      aria-label={getAriaLabel()}
      title={getAriaLabel()}
    >
      {getIcon()}
    </button>
  );
};

export default CopyButton;