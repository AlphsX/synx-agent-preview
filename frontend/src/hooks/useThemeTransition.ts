'use client';

import { useEffect, useRef, useState } from 'react';
import { useDarkMode } from './useDarkMode';

export interface ThemeTransitionConfig {
  duration?: number;
  easing?: string;
  enableViewTransition?: boolean;
}

export const useThemeTransition = (config: ThemeTransitionConfig = {}) => {
  const {
    duration = 300,
    easing = 'cubic-bezier(0.4, 0, 0.2, 1)',
    enableViewTransition = true,
  } = config;

  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const transitionRef = useRef<number | null>(null);

  // Enhanced theme toggle with smooth transitions
  const toggleThemeWithTransition = async () => {
    if (isTransitioning) return;

    setIsTransitioning(true);

    // Use View Transitions API if available and enabled
    if (enableViewTransition && 'startViewTransition' in document) {
      try {
        // @ts-ignore - View Transitions API is experimental
        await document.startViewTransition(() => {
          toggleDarkMode();
        }).finished;
      } catch (error) {
        console.warn('View transition failed, falling back to regular transition:', error);
        toggleDarkMode();
      }
    } else {
      // Fallback to custom transition
      await performCustomTransition();
    }

    setIsTransitioning(false);
  };

  // Custom transition implementation
  const performCustomTransition = async (): Promise<void> => {
    return new Promise((resolve) => {
      // Create transition overlay
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: ${isDarkMode ? '#ffffff' : '#000000'};
        opacity: 0;
        pointer-events: none;
        z-index: 9999;
        transition: opacity ${duration}ms ${easing};
      `;
      
      document.body.appendChild(overlay);

      // Fade in overlay
      requestAnimationFrame(() => {
        overlay.style.opacity = '0.1';
      });

      // Toggle theme at midpoint
      setTimeout(() => {
        toggleDarkMode();
        
        // Fade out overlay
        setTimeout(() => {
          overlay.style.opacity = '0';
          
          // Remove overlay after transition
          setTimeout(() => {
            document.body.removeChild(overlay);
            resolve();
          }, duration);
        }, 50);
      }, duration / 2);
    });
  };

  // Apply transition styles to root element
  useEffect(() => {
    const root = document.documentElement;
    
    if (isTransitioning) {
      root.style.setProperty('--theme-transition-duration', `${duration}ms`);
      root.style.setProperty('--theme-transition-easing', easing);
      root.classList.add('theme-transitioning');
    } else {
      root.classList.remove('theme-transitioning');
    }

    return () => {
      root.classList.remove('theme-transitioning');
    };
  }, [isTransitioning, duration, easing]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (transitionRef.current) {
        cancelAnimationFrame(transitionRef.current);
      }
    };
  }, []);

  return {
    isDarkMode,
    isTransitioning,
    toggleThemeWithTransition,
    toggleDarkMode, // Direct toggle without transition
  };
};

// CSS-in-JS styles for theme transitions
export const getThemeTransitionStyles = () => `
  .theme-transitioning * {
    transition-property: background-color, border-color, color, fill, stroke, opacity, box-shadow, transform, filter, backdrop-filter !important;
    transition-duration: var(--theme-transition-duration, 300ms) !important;
    transition-timing-function: var(--theme-transition-easing, cubic-bezier(0.4, 0, 0.2, 1)) !important;
  }

  .theme-transitioning *:before,
  .theme-transitioning *:after {
    transition-property: background-color, border-color, color, fill, stroke, opacity, box-shadow, transform, filter, backdrop-filter !important;
    transition-duration: var(--theme-transition-duration, 300ms) !important;
    transition-timing-function: var(--theme-transition-easing, cubic-bezier(0.4, 0, 0.2, 1)) !important;
  }

  /* View Transitions API support */
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation-duration: var(--theme-transition-duration, 300ms);
    animation-timing-function: var(--theme-transition-easing, cubic-bezier(0.4, 0, 0.2, 1));
  }

  ::view-transition-old(root) {
    animation-name: theme-fade-out;
  }

  ::view-transition-new(root) {
    animation-name: theme-fade-in;
  }

  @keyframes theme-fade-out {
    from {
      opacity: 1;
    }
    to {
      opacity: 0;
    }
  }

  @keyframes theme-fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    .theme-transitioning * {
      transition-duration: 0.01ms !important;
    }
    
    ::view-transition-old(root),
    ::view-transition-new(root) {
      animation-duration: 0.01ms !important;
    }
  }
`;

// Hook for managing theme transition preferences
export const useThemeTransitionPreferences = () => {
  const [preferences, setPreferences] = useState({
    enableTransitions: true,
    transitionDuration: 300,
    enableViewTransitions: true,
  });

  useEffect(() => {
    // Load preferences from localStorage
    const saved = localStorage.getItem('theme-transition-preferences');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setPreferences(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.warn('Failed to parse theme transition preferences:', error);
      }
    }
  }, []);

  const updatePreferences = (updates: Partial<typeof preferences>) => {
    const newPreferences = { ...preferences, ...updates };
    setPreferences(newPreferences);
    localStorage.setItem('theme-transition-preferences', JSON.stringify(newPreferences));
  };

  return {
    preferences,
    updatePreferences,
  };
};