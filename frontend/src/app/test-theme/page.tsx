'use client';

import { useDarkMode } from '@/hooks/useDarkMode';
import { useEffect } from 'react';

export default function TestThemePage() {
  const { isDarkMode, toggleDarkMode, resetToSystemPreference } = useDarkMode();

  // Log system preference changes for testing
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const logSystemPreference = (e: MediaQueryListEvent) => {
      console.log('System preference changed:', e.matches ? 'dark' : 'light');
    };
    
    mediaQuery.addEventListener('change', logSystemPreference);
    
    return () => {
      mediaQuery.removeEventListener('change', logSystemPreference);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <h1 className="text-3xl font-bold mb-8">Theme Testing</h1>
      
      <div className="mb-8 p-6 rounded-xl bg-gray-100 dark:bg-gray-800 shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Current Theme Status</h2>
        <p className="text-lg mb-2">Dark Mode: <span className="font-mono">{isDarkMode ? 'enabled' : 'disabled'}</span></p>
        <p className="text-lg">System Preference: <span className="font-mono">
          {window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'}
        </span></p>
      </div>
      
      <div className="flex gap-4">
        <button 
          onClick={toggleDarkMode}
          className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
        >
          Toggle Theme
        </button>
        
        <button 
          onClick={resetToSystemPreference}
          className="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
        >
          Reset to System Preference
        </button>
      </div>
      
      <div className="mt-8 text-sm text-gray-500 dark:text-gray-400">
        <p>Test instructions:</p>
        <ol className="list-decimal list-inside mt-2 space-y-1">
          <li>Check if the theme matches your system preference</li>
          <li>Toggle the theme manually</li>
          <li>Change your system theme and see if it updates automatically (when not manually set)</li>
          <li>Reset to system preference and test again</li>
        </ol>
      </div>
    </div>
  );
}