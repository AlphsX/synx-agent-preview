import { useState, useEffect, useRef, useCallback } from "react";

interface UseIdleDetectionOptions {
  idleTime?: number; // milliseconds, default 3000
  events?: string[]; // events to track
}

interface UseIdleDetectionReturn {
  isIdle: boolean;
}

/**
 * Custom hook to detect user inactivity
 * @param options Configuration options for idle detection
 * @returns Object containing isIdle state
 */
export function useIdleDetection(
  options: UseIdleDetectionOptions = {}
): UseIdleDetectionReturn {
  const {
    idleTime = 3000,
    events = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"],
  } = options;

  const [isIdle, setIsIdle] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Clear existing timer
  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Clear debounce timer
  const clearDebounceTimer = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
  }, []);

  // Start idle timer
  const startTimer = useCallback(() => {
    clearTimer();
    timerRef.current = setTimeout(() => {
      setIsIdle(true);
    }, idleTime);
  }, [idleTime, clearTimer]);

  // Handle user activity with debouncing
  const handleActivity = useCallback(() => {
    // Clear debounce timer
    clearDebounceTimer();

    // Debounce state updates to prevent excessive re-renders
    debounceTimerRef.current = setTimeout(() => {
      // If currently idle, immediately set to not idle
      setIsIdle((prevIdle) => {
        if (prevIdle) {
          return false;
        }
        return prevIdle;
      });

      // Restart the idle timer
      startTimer();
    }, 100); // 100ms debounce
  }, [startTimer, clearDebounceTimer]);

  useEffect(() => {
    // Only run on client-side
    if (typeof window === "undefined") return;

    // Start initial timer
    startTimer();

    // Attach event listeners
    const attachListeners = () => {
      try {
        events.forEach((event) => {
          window.addEventListener(event, handleActivity, { passive: true });
        });
      } catch (error) {
        console.error(
          "Failed to attach idle detection event listeners:",
          error
        );
      }
    };

    attachListeners();

    // Cleanup function
    return () => {
      clearTimer();
      clearDebounceTimer();

      // Remove event listeners only if window exists
      if (typeof window !== "undefined") {
        events.forEach((event) => {
          window.removeEventListener(event, handleActivity);
        });
      }
    };
  }, [events, handleActivity, startTimer, clearTimer, clearDebounceTimer]);

  return { isIdle };
}
