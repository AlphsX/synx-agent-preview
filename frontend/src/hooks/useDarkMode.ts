'use client';

import { useState, useEffect } from 'react';

export function useDarkMode() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true); // Default to dark mode
  const [systemPreference, setSystemPreference] = useState<boolean>(true);
  const [userPreference, setUserPreference] = useState<boolean | null>(null);

  useEffect(() => {
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
      if (userPreference === null) {
        setIsDarkMode(e.matches);
      }
    };
    
    // Use addEventListener for better browser compatibility
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [userPreference]);

  useEffect(() => {
    // Apply theme to document
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    setUserPreference(newMode);
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
  };

  // Add a function to reset to system preference
  const resetToSystemPreference = () => {
    localStorage.removeItem('theme');
    setUserPreference(null);
    setIsDarkMode(systemPreference);
  };

  return { isDarkMode, toggleDarkMode, resetToSystemPreference };
}