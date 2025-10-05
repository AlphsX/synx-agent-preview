'use client';

import { useEffect, useRef, useCallback } from 'react';

interface SwipeGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number; // Minimum distance for a swipe
  velocityThreshold?: number; // Minimum velocity for a swipe
  preventScroll?: boolean; // Prevent default scroll behavior
}

export function useSwipeGesture(options: SwipeGestureOptions) {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    threshold = 50,
    velocityThreshold = 0.3,
    preventScroll = false
  } = options;

  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const elementRef = useRef<HTMLElement | null>(null);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (e.touches.length !== 1) return;
    
    const touch = e.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now()
    };
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (preventScroll && touchStartRef.current) {
      // Prevent default scroll behavior during swipe
      e.preventDefault();
    }
  }, [preventScroll]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (!touchStartRef.current || e.changedTouches.length !== 1) return;

    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const deltaTime = Date.now() - touchStartRef.current.time;
    
    // Calculate distance and velocity
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    const velocity = distance / deltaTime;

    // Check if swipe meets threshold requirements
    if (distance < threshold || velocity < velocityThreshold) {
      touchStartRef.current = null;
      return;
    }

    // Determine swipe direction based on the larger delta
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    if (absDeltaX > absDeltaY) {
      // Horizontal swipe
      if (deltaX > 0 && onSwipeRight) {
        onSwipeRight();
      } else if (deltaX < 0 && onSwipeLeft) {
        onSwipeLeft();
      }
    } else {
      // Vertical swipe
      if (deltaY > 0 && onSwipeDown) {
        onSwipeDown();
      } else if (deltaY < 0 && onSwipeUp) {
        onSwipeUp();
      }
    }

    touchStartRef.current = null;
  }, [onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, threshold, velocityThreshold]);

  const attachToElement = useCallback((element: HTMLElement | null) => {
    // Remove previous listeners
    if (elementRef.current) {
      elementRef.current.removeEventListener('touchstart', handleTouchStart);
      elementRef.current.removeEventListener('touchmove', handleTouchMove);
      elementRef.current.removeEventListener('touchend', handleTouchEnd);
    }

    // Attach new listeners
    if (element) {
      elementRef.current = element;
      element.addEventListener('touchstart', handleTouchStart, { passive: !preventScroll });
      element.addEventListener('touchmove', handleTouchMove, { passive: !preventScroll });
      element.addEventListener('touchend', handleTouchEnd, { passive: true });
    }
  }, [handleTouchStart, handleTouchMove, handleTouchEnd, preventScroll]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (elementRef.current) {
        elementRef.current.removeEventListener('touchstart', handleTouchStart);
        elementRef.current.removeEventListener('touchmove', handleTouchMove);
        elementRef.current.removeEventListener('touchend', handleTouchEnd);
      }
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return { attachToElement };
}