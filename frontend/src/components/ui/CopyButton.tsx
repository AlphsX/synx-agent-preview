'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Check, Copy, AlertCircle } from 'lucide-react';
import { createScaleAnimation, createBounceAnimation, useOptimizedAnimation } from '@/lib/animation-utils';

export interface CopyButtonProps {
  text: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'ghost' | 'outline';
  onCopy?: (text: string) => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
  'aria-label'?: string;
  showTooltip?: boolean;
  enableHapticFeedback?: boolean;
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
  showTooltip = true,
  enableHapticFeedback = true,
}) => {
  const [copyState, setCopyState] = useState<CopyState>('idle');
  const [isHovered, setIsHovered] = useState(false);
  const [showRipple, setShowRipple] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const rippleRef = useRef<HTMLDivElement>(null);
  const { shouldAnimate, getAnimationProps } = useOptimizedAnimation();

  // Haptic feedback for mobile devices
  const triggerHapticFeedback = useCallback(() => {
    if (enableHapticFeedback && 'vibrate' in navigator) {
      navigator.vibrate(50);
    }
  }, [enableHapticFeedback]);

  // Enhanced copy functionality with animations
  const handleCopy = useCallback(async (event?: React.MouseEvent) => {
    if (disabled || copyState === 'copying') return;

    // Trigger haptic feedback
    triggerHapticFeedback();

    // Create ripple effect for touch interactions
    if (event && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      if (rippleRef.current) {
        rippleRef.current.style.left = `${x}px`;
        rippleRef.current.style.top = `${y}px`;
        setShowRipple(true);
        setTimeout(() => setShowRipple(false), 600);
      }
    }

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

      // Reset to idle after 2 seconds with smooth transition
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
  }, [text, disabled, copyState, onCopy, onError, triggerHapticFeedback]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleCopy();
    }
  }, [handleCopy]);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
  }, []);

  // Size classes with enhanced spacing
  const sizeClasses = {
    sm: 'h-7 w-7 p-1.5',
    md: 'h-9 w-9 p-2',
    lg: 'h-11 w-11 p-2.5',
  };

  // Enhanced variant classes with better visual hierarchy
  const variantClasses = {
    default: `
      bg-gray-100/80 hover:bg-gray-200/90 dark:bg-gray-700/80 dark:hover:bg-gray-600/90
      backdrop-blur-sm border border-gray-200/50 dark:border-gray-600/50
      shadow-sm hover:shadow-md
    `,
    ghost: `
      hover:bg-gray-100/80 dark:hover:bg-gray-700/80
      backdrop-blur-sm
    `,
    outline: `
      border-2 border-gray-300/60 hover:border-gray-400/80 hover:bg-gray-50/80 
      dark:border-gray-600/60 dark:hover:border-gray-500/80 dark:hover:bg-gray-700/80
      backdrop-blur-sm
    `,
  };

  // Enhanced state-specific classes with smooth transitions
  const stateClasses = {
    idle: '',
    copying: 'opacity-75 cursor-wait scale-95',
    success: `
      bg-green-100/90 hover:bg-green-200/90 dark:bg-green-900/80 dark:hover:bg-green-800/90 
      text-green-700 dark:text-green-300 border-green-300/60 dark:border-green-600/60
      shadow-green-200/50 dark:shadow-green-900/50 shadow-lg
      animate-copy-success
    `,
    error: `
      bg-red-100/90 hover:bg-red-200/90 dark:bg-red-900/80 dark:hover:bg-red-800/90 
      text-red-700 dark:text-red-300 border-red-300/60 dark:border-red-600/60
      shadow-red-200/50 dark:shadow-red-900/50 shadow-lg
    `,
  };

  // Icon size classes
  const iconSizeClasses = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const getIcon = () => {
    const iconClass = `${iconSizeClasses[size]} transition-all duration-200`;
    
    switch (copyState) {
      case 'copying':
        return <Copy className={`${iconClass} animate-pulse`} />;
      case 'success':
        return <Check className={`${iconClass} animate-bounce-in`} />;
      case 'error':
        return <AlertCircle className={`${iconClass} animate-bounce-in`} />;
      default:
        return <Copy className={iconClass} />;
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

  const getTooltipText = () => {
    switch (copyState) {
      case 'copying':
        return 'Copying...';
      case 'success':
        return 'Copied!';
      case 'error':
        return 'Copy failed';
      default:
        return 'Copy to clipboard';
    }
  };

  return (
    <div className="relative inline-block">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleCopy}
        onKeyDown={handleKeyDown}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        disabled={disabled || copyState === 'copying'}
        className={`
          relative inline-flex items-center justify-center
          rounded-lg overflow-hidden
          transition-all duration-300 ease-out-back
          focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2
          dark:focus:ring-offset-gray-800
          disabled:opacity-50 disabled:cursor-not-allowed
          transform-gpu will-change-transform
          ${sizeClasses[size]}
          ${variantClasses[variant]}
          ${stateClasses[copyState]}
          ${isHovered && copyState === 'idle' ? 'scale-105 shadow-lg' : ''}
          ${shouldAnimate ? 'gpu-accelerated' : ''}
          ${className}
        `}
        aria-label={getAriaLabel()}
        title={getAriaLabel()}
        {...getAnimationProps(createScaleAnimation(1.05))}
      >
        {/* Ripple effect for touch interactions */}
        <div
          ref={rippleRef}
          className={`
            absolute w-0 h-0 rounded-full pointer-events-none
            bg-white/30 dark:bg-gray-300/30
            transition-all duration-600 ease-out
            ${showRipple ? 'w-20 h-20 -translate-x-10 -translate-y-10' : ''}
          `}
        />
        
        {/* Icon with enhanced animations */}
        <div className="relative z-10">
          {getIcon()}
        </div>
        
        {/* Glow effect for success state */}
        {copyState === 'success' && shouldAnimate && (
          <div className="absolute inset-0 rounded-lg animate-glow-pulse bg-green-400/20 dark:bg-green-500/20" />
        )}
      </button>

      {/* Enhanced tooltip */}
      {showTooltip && isHovered && (
        <div
          className={`
            absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2
            px-3 py-1.5 text-xs font-medium text-white
            bg-gray-900/90 dark:bg-gray-100/90 dark:text-gray-900
            rounded-lg shadow-lg backdrop-blur-sm
            pointer-events-none z-50
            transition-all duration-200 ease-out
            ${shouldAnimate ? 'animate-fade-in-up' : ''}
          `}
        >
          {getTooltipText()}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900/90 dark:border-t-gray-100/90" />
        </div>
      )}
    </div>
  );
};

export default CopyButton;