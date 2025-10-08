'use client';

import { useState, useEffect } from 'react';

export function useDarkMode() {
  // Initialize with false to prevent hydration mismatch
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);
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
    
    // Small delay to ensure layout.tsx script has run
    setTimeout(() => {
      // Get what the document class actually is (set by layout.tsx)
      const actualDocumentDark = document.documentElement.classList.contains('dark');
      
      // Get system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setSystemPreference(prefersDark);
      
      // Get localStorage theme
      const savedTheme = localStorage.getItem('theme');
      
      // Set user preference based on saved theme
      if (savedTheme === 'dark') {
        setUserPreference(true);
      } else if (savedTheme === 'light') {
        setUserPreference(false);
      } else {
        setUserPreference(null); // system
      }
      
      // Simply sync our state with what the document actually is
      setIsDarkMode(actualDocumentDark);
      
      // Debug log for mobile
      if (window.innerWidth < 768) {
        console.log('Mobile Theme Sync:', {
          savedTheme,
          prefersDark,
          actualDocumentDark,
          syncing: 'state to match document'
        });
      }
    }, 50); // Small delay to ensure layout script runs first
    
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
    
    // Don't listen for document class changes to avoid conflicts with layout.tsx script
    // The state should only be updated by this hook or system preference changes
    
    // Use addEventListener for better browser compatibility
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  const toggleDarkMode = () => {
    if (typeof window === 'undefined') return;
    
    const newMode = !isDarkMode;
    
    // Update localStorage first
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
    
    // Update document class immediately
    document.documentElement.classList.remove('dark');
    if (newMode) {
      document.documentElement.classList.add('dark');
    }
    
    // Update states
    setIsDarkMode(newMode);
    setUserPreference(newMode);
    
    // Debug log for mobile
    if (window.innerWidth < 768) {
      console.log('Theme Toggle:', {
        newMode,
        localStorage: localStorage.getItem('theme'),
        documentHasDark: document.documentElement.classList.contains('dark')
      });
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