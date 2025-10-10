'use client';

import { useCallback, useRef, useState, useEffect } from 'react';

export interface TouchInteractionConfig {
  enableHapticFeedback?: boolean;
  enableRippleEffect?: boolean;
  rippleColor?: string;
  touchFeedbackDuration?: number;
  swipeThreshold?: number;
  longPressDelay?: number;
}

export interface TouchState {
  isPressed: boolean;
  isSwiping: boolean;
  swipeDirection: 'left' | 'right' | 'up' | 'down' | null;
  isLongPress: boolean;
  touchPosition: { x: number; y: number } | null;
}

export interface SwipeGesture {
  direction: 'left' | 'right' | 'up' | 'down';
  distance: number;
  velocity: number;
  duration: number;
}

export const useTouchInteractions = (config: TouchInteractionConfig = {}) => {
  const {
    enableHapticFeedback = true,
    enableRippleEffect = true,
    rippleColor = 'rgba(255, 255, 255, 0.3)',
    touchFeedbackDuration = 150,
    swipeThreshold = 50,
    longPressDelay = 500,
  } = config;

  const [touchState, setTouchState] = useState<TouchState>({
    isPressed: false,
    isSwiping: false,
    swipeDirection: null,
    isLongPress: false,
    touchPosition: null,
  });

  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const rippleElementRef = useRef<HTMLDivElement | null>(null);

  // Haptic feedback utility
  const triggerHapticFeedback = useCallback((type: 'light' | 'medium' | 'heavy' = 'light') => {
    if (!enableHapticFeedback) return;

    if ('vibrate' in navigator) {
      const patterns = {
        light: 10,
        medium: 50,
        heavy: 100,
      };
      navigator.vibrate(patterns[type]);
    }
  }, [enableHapticFeedback]);

  // Create ripple effect
  const createRippleEffect = useCallback((element: HTMLElement, x: number, y: number) => {
    if (!enableRippleEffect) return;

    const rect = element.getBoundingClientRect();
    const ripple = document.createElement('div');
    const size = Math.max(rect.width, rect.height) * 2;

    ripple.style.cssText = `
      position: absolute;
      left: ${x - rect.left - size / 2}px;
      top: ${y - rect.top - size / 2}px;
      width: ${size}px;
      height: ${size}px;
      background: ${rippleColor};
      border-radius: 50%;
      pointer-events: none;
      transform: scale(0);
      opacity: 0.6;
      animation: ripple-animation 600ms ease-out;
      z-index: 1000;
    `;

    // Add ripple animation keyframes if not already present
    if (!document.querySelector('#ripple-styles')) {
      const style = document.createElement('style');
      style.id = 'ripple-styles';
      style.textContent = `
        @keyframes ripple-animation {
          0% {
            transform: scale(0);
            opacity: 0.6;
          }
          100% {
            transform: scale(1);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }

    element.style.position = element.style.position || 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);

    // Remove ripple after animation
    setTimeout(() => {
      if (ripple.parentNode) {
        ripple.parentNode.removeChild(ripple);
      }
    }, 600);
  }, [enableRippleEffect, rippleColor]);

  // Touch start handler
  const handleTouchStart = useCallback((event: TouchEvent) => {
    const touch = event.touches[0];
    const target = event.currentTarget as HTMLElement;

    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };

    setTouchState(prev => ({
      ...prev,
      isPressed: true,
      touchPosition: { x: touch.clientX, y: touch.clientY },
    }));

    // Create ripple effect
    createRippleEffect(target, touch.clientX, touch.clientY);

    // Light haptic feedback on touch start
    triggerHapticFeedback('light');

    // Start long press timer
    longPressTimerRef.current = setTimeout(() => {
      setTouchState(prev => ({ ...prev, isLongPress: true }));
      triggerHapticFeedback('medium');
    }, longPressDelay);
  }, [createRippleEffect, triggerHapticFeedback, longPressDelay]);

  // Touch move handler
  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (!touchStartRef.current) return;

    const touch = event.touches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Clear long press timer if moving
    if (longPressTimerRef.current && distance > 10) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
      setTouchState(prev => ({ ...prev, isLongPress: false }));
    }

    // Detect swipe direction
    if (distance > swipeThreshold) {
      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);
      let direction: 'left' | 'right' | 'up' | 'down';

      if (absX > absY) {
        direction = deltaX > 0 ? 'right' : 'left';
      } else {
        direction = deltaY > 0 ? 'down' : 'up';
      }

      setTouchState(prev => ({
        ...prev,
        isSwiping: true,
        swipeDirection: direction,
        touchPosition: { x: touch.clientX, y: touch.clientY },
      }));
    }
  }, [swipeThreshold]);

  // Touch end handler
  const handleTouchEnd = useCallback((event: TouchEvent) => {
    if (!touchStartRef.current) return;

    const endTime = Date.now();
    const duration = endTime - touchStartRef.current.time;
    
    // Calculate swipe velocity if swiping
    let swipeGesture: SwipeGesture | null = null;
    if (touchState.isSwiping && touchState.swipeDirection) {
      const touch = event.changedTouches[0];
      const deltaX = touch.clientX - touchStartRef.current.x;
      const deltaY = touch.clientY - touchStartRef.current.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      const velocity = distance / duration;

      swipeGesture = {
        direction: touchState.swipeDirection,
        distance,
        velocity,
        duration,
      };
    }

    // Clear timers
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // Reset touch state
    setTouchState({
      isPressed: false,
      isSwiping: false,
      swipeDirection: null,
      isLongPress: false,
      touchPosition: null,
    });

    touchStartRef.current = null;

    return swipeGesture;
  }, [touchState.isSwiping, touchState.swipeDirection]);

  // Touch cancel handler
  const handleTouchCancel = useCallback(() => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    setTouchState({
      isPressed: false,
      isSwiping: false,
      swipeDirection: null,
      isLongPress: false,
      touchPosition: null,
    });

    touchStartRef.current = null;
  }, []);

  // Enhanced touch event handlers with gesture recognition
  const getTouchHandlers = useCallback((callbacks?: {
    onTap?: () => void;
    onLongPress?: () => void;
    onSwipe?: (gesture: SwipeGesture) => void;
    onTouchStart?: () => void;
    onTouchEnd?: () => void;
  }) => {
    return {
      onTouchStart: (event: React.TouchEvent) => {
        handleTouchStart(event.nativeEvent);
        callbacks?.onTouchStart?.();
      },
      onTouchMove: (event: React.TouchEvent) => {
        handleTouchMove(event.nativeEvent);
      },
      onTouchEnd: (event: React.TouchEvent) => {
        const swipeGesture = handleTouchEnd(event.nativeEvent);
        
        if (swipeGesture) {
          callbacks?.onSwipe?.(swipeGesture);
        } else if (touchState.isLongPress) {
          callbacks?.onLongPress?.();
        } else if (!touchState.isSwiping) {
          callbacks?.onTap?.();
        }
        
        callbacks?.onTouchEnd?.();
      },
      onTouchCancel: () => {
        handleTouchCancel();
      },
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd, handleTouchCancel, touchState]);

  // Get touch feedback styles
  const getTouchFeedbackStyles = useCallback(() => {
    return {
      transform: touchState.isPressed ? 'scale(0.98)' : 'scale(1)',
      transition: `transform ${touchFeedbackDuration}ms ease-out`,
      userSelect: 'none' as const,
      WebkitUserSelect: 'none' as const,
      WebkitTouchCallout: 'none' as const,
      WebkitTapHighlightColor: 'transparent',
    };
  }, [touchState.isPressed, touchFeedbackDuration]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
    };
  }, []);

  return {
    touchState,
    getTouchHandlers,
    getTouchFeedbackStyles,
    triggerHapticFeedback,
    createRippleEffect,
  };
};

// Hook for detecting mobile device and touch capabilities
export const useMobileDetection = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [hasTouch, setHasTouch] = useState(false);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');

  useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const mobileKeywords = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone',
        'miui', 'harmonyos', 'hyperos', 'emui', 'funtouch', 'coloros', 'oxygenos', 'oneui',
        'samsung', 'xiaomi', 'huawei', 'oppo', 'vivo', 'oneplus', 'realme'
      ];
      const isMobileDevice = mobileKeywords.some(keyword => userAgent.includes(keyword));
      
      setIsMobile(isMobileDevice || window.innerWidth <= 768);
      setHasTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
    };

    const checkOrientation = () => {
      setOrientation(window.innerHeight > window.innerWidth ? 'portrait' : 'landscape');
    };

    checkMobile();
    checkOrientation();

    window.addEventListener('resize', checkMobile);
    window.addEventListener('resize', checkOrientation);
    window.addEventListener('orientationchange', checkOrientation);

    return () => {
      window.removeEventListener('resize', checkMobile);
      window.removeEventListener('resize', checkOrientation);
      window.removeEventListener('orientationchange', checkOrientation);
    };
  }, []);

  return {
    isMobile,
    hasTouch,
    orientation,
  };
};