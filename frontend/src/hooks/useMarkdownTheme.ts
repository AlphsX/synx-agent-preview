'use client';

import { useMemo, useEffect, useState } from 'react';
import { MarkdownTheme } from '@/types/markdown';
import { DEFAULT_MARKDOWN_THEME } from '@/constants/markdown';

export interface UseMarkdownThemeOptions {
  customTheme?: Partial<MarkdownTheme>;
  respectSystemTheme?: boolean;
}

export function useMarkdownTheme(options: UseMarkdownThemeOptions = {}) {
  const { customTheme, respectSystemTheme = true } = options;
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Listen for theme changes
  useEffect(() => {
    if (!respectSystemTheme) return;

    const updateTheme = () => {
      const isDark = document.documentElement.classList.contains('dark') ||
                    (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
      setIsDarkMode(isDark);
    };

    // Initial check
    updateTheme();

    // Listen for class changes on document element
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          updateTheme();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleMediaChange = () => updateTheme();
    
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleMediaChange);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleMediaChange);
    }

    return () => {
      observer.disconnect();
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleMediaChange);
      } else {
        mediaQuery.removeListener(handleMediaChange);
      }
    };
  }, [respectSystemTheme]);

  // Generate theme-aware markdown theme
  const markdownTheme = useMemo(() => {
    const baseTheme = { ...DEFAULT_MARKDOWN_THEME };
    
    // Apply custom theme overrides
    if (customTheme) {
      if (customTheme.typography) {
        baseTheme.typography = { ...baseTheme.typography, ...customTheme.typography };
      }
      if (customTheme.colors) {
        baseTheme.colors = { ...baseTheme.colors, ...customTheme.colors };
      }
      if (customTheme.spacing) {
        baseTheme.spacing = { ...baseTheme.spacing, ...customTheme.spacing };
      }
    }

    return baseTheme;
  }, [customTheme]);

  // Generate CSS custom properties for dynamic theming
  const cssVariables = useMemo(() => {
    const vars: Record<string, string> = {};
    
    // Convert theme colors to CSS variables
    Object.entries(markdownTheme.colors).forEach(([key, value]) => {
      vars[`--markdown-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`] = value;
    });

    // Convert spacing to CSS variables
    Object.entries(markdownTheme.spacing).forEach(([key, value]) => {
      vars[`--markdown-spacing-${key}`] = value;
    });

    return vars;
  }, [markdownTheme]);

  // Apply CSS variables to document
  useEffect(() => {
    const root = document.documentElement;
    
    Object.entries(cssVariables).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });

    return () => {
      Object.keys(cssVariables).forEach((property) => {
        root.style.removeProperty(property);
      });
    };
  }, [cssVariables]);

  return {
    theme: markdownTheme,
    isDarkMode,
    cssVariables,
    // Helper functions
    getHeadingClass: (level: number) => {
      const headingKey = `h${level}` as keyof typeof markdownTheme.typography.headings;
      return markdownTheme.typography.headings[headingKey] || '';
    },
    getColorClass: (colorKey: keyof typeof markdownTheme.colors) => {
      return markdownTheme.colors[colorKey] || '';
    },
    getSpacingClass: (spacingKey: keyof typeof markdownTheme.spacing) => {
      return markdownTheme.spacing[spacingKey] || '';
    }
  };
}

// Hook for syntax highlighting theme
export function useSyntaxHighlightingTheme() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    const updateTheme = () => {
      const isDark = document.documentElement.classList.contains('dark') ||
                    (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
      setIsDarkMode(isDark);
    };

    updateTheme();

    const observer = new MutationObserver(updateTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleMediaChange = () => updateTheme();
    
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleMediaChange);
    } else {
      mediaQuery.addListener(handleMediaChange);
    }

    return () => {
      observer.disconnect();
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleMediaChange);
      } else {
        mediaQuery.removeListener(handleMediaChange);
      }
    };
  }, []);

  return {
    isDarkMode,
    // Theme names for react-syntax-highlighter
    themeName: isDarkMode ? 'oneDark' : 'oneLight',
    // Custom theme properties
    backgroundColor: isDarkMode ? '#1f2937' : '#f9fafb',
    textColor: isDarkMode ? '#e5e7eb' : '#374151',
    borderColor: isDarkMode ? '#374151' : '#e5e7eb'
  };
}