'use client';

import { useState, useEffect } from 'react';

export function useDarkMode() {
  // Get initial theme from document class (set by layout.tsx script)
  const getInitialTheme = () => {
    if (typeof window === 'undefined') return false;
    return document.documentElement.classList.contains('dark');
  };

  const [isDarkMode, setIsDarkMode] = useState<boolean>(getInitialTheme);
  const [systemPreference, setSystemPreference] = useState<boolean>(false);
  const [userPreference, setUserPreference] = useState<boolean | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  // Check if currently using system preference (no user override)
  const isUsingSystemPreference = userPreference === null;

  useEffect(() => {
    // Mark as hydrated to prevent hydration mismatch
    setIsHydrated(true);
    
    // Only run client-side code after hydration
    if (typeof window === 'undefined') return;
    
    // Get initial system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setSystemPreference(prefersDark);
    
    // Check localStorage for user preference
    const savedTheme = localStorage.getItem('theme');
    
    // If no theme is set, default to system preference
    if (!savedTheme) {
      localStorage.setItem('theme', 'system');
    }
    
    // Set user preference based on saved theme
    if (savedTheme === 'dark') {
      setUserPreference(true);
    } else if (savedTheme === 'light') {
      setUserPreference(false);
    } else {
      setUserPreference(null); // system
    }
    
    // Sync with document class (set by layout.tsx)
    setIsDarkMode(document.documentElement.classList.contains('dark'));
    
    // Listen for system preference changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemPreference(e.matches);
      // Only update theme if user is using system preference
      const currentUserPref = localStorage.getItem('theme');
      if (!currentUserPref || currentUserPref === 'system') {
        setIsDarkMode(e.matches);
        // Update document class
        if (e.matches) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    };
    
    // Listen for document class changes (from other sources)
    const observer = new MutationObserver(() => {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });
    
    // Use addEventListener for better browser compatibility
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
      observer.disconnect();
    };
  }, []);

  const toggleDarkMode = () => {
    if (typeof window === 'undefined') return;
    
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    setUserPreference(newMode);
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
    
    // Update document class immediately
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Add a function to reset to system preference
  const resetToSystemPreference = () => {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem('theme', 'system');
    setUserPreference(null);
    setIsDarkMode(systemPreference);
    
    // Update document class based on system preference
    if (systemPreference) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return { 
    isDarkMode, 
    toggleDarkMode, 
    resetToSystemPreference, 
    isUsingSystemPreference,
    systemPreference,
    isHydrated 
  };
}