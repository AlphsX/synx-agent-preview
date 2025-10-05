'use client';

import { useState, useEffect } from 'react';

export function useDarkMode() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false); // Start with false to match SSR
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
    
    if (savedTheme && savedTheme !== 'system') {
      // User has manually set a preference
      const savedValue = savedTheme === 'dark';
      setIsDarkMode(savedValue);
      setUserPreference(savedValue);
    } else {
      // Use system preference as default
      setIsDarkMode(prefersDark);
      setUserPreference(null);
      // Ensure localStorage reflects system preference as default
      if (!savedTheme) {
        localStorage.setItem('theme', 'system');
      }
    }
    
    // Listen for system preference changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemPreference(e.matches);
      // Only update theme if user is using system preference
      const currentUserPref = localStorage.getItem('theme');
      if (!currentUserPref || currentUserPref === 'system') {
        setIsDarkMode(e.matches);
      }
    };
    
    // Use addEventListener for better browser compatibility
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

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
    
    localStorage.setItem('theme', 'system');
    setUserPreference(null);
    setIsDarkMode(systemPreference);
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