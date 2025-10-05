'use client';

import { useState, useEffect } from 'react';

export function useDarkMode() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false); // Start with false to match SSR
  const [systemPreference, setSystemPreference] = useState<boolean>(false);
  const [userPreference, setUserPreference] = useState<boolean | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Mark as hydrated to prevent hydration mismatch
    setIsHydrated(true);
    
    // Only run client-side code after hydration
    if (typeof window === 'undefined') return;
    
    // Check localStorage for user preference
    const savedTheme = localStorage.getItem('theme');
    
    // Get initial system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setSystemPreference(prefersDark);
    
    if (savedTheme) {
      const savedValue = savedTheme === 'dark';
      setIsDarkMode(savedValue);
      setUserPreference(savedValue);
    } else {
      setIsDarkMode(prefersDark);
      setUserPreference(null);
    }
    
    // Listen for system preference changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemPreference(e.matches);
      // Only update theme if user hasn't manually set a preference
      const currentUserPref = localStorage.getItem('theme');
      if (!currentUserPref) {
        setIsDarkMode(e.matches);
      }
    };
    
    // Use addEventListener for better browser compatibility
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []); // Remove userPreference from dependency array to prevent infinite loop

  useEffect(() => {
    // Only apply theme to document after hydration
    if (!isHydrated || typeof window === 'undefined') return;
    
    // Apply theme to document
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode, isHydrated]);

  const toggleDarkMode = () => {
    if (typeof window === 'undefined') return;
    
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    setUserPreference(newMode);
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
  };

  // Add a function to reset to system preference
  const resetToSystemPreference = () => {
    if (typeof window === 'undefined') return;
    
    localStorage.removeItem('theme');
    setUserPreference(null);
    setIsDarkMode(systemPreference);
  };

  return { isDarkMode, toggleDarkMode, resetToSystemPreference, isHydrated };
}