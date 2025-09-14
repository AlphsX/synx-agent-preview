'use client';

import { useState, useEffect } from 'react';
import { useDarkMode } from '@/hooks/useDarkMode';

export default function TestSystemTheme() {
  const { isDarkMode, toggleDarkMode, resetToSystemPreference } = useDarkMode();
  const [systemPreference, setSystemPreference] = useState<'dark' | 'light'>('dark');

  // Track system preference changes
  useEffect(() => {
    const updateSystemPreference = () => {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setSystemPreference(prefersDark ? 'dark' : 'light');
    };

    // Initial check
    updateSystemPreference();

    // Listen for changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', updateSystemPreference);

    return () => {
      mediaQuery.removeEventListener('change', updateSystemPreference);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div className="max-w-md w-full space-y-6">
        <h1 className="text-3xl font-bold text-center">System Theme Test</h1>
        
        <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4">Theme Status</h2>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>Current Theme:</span>
              <span className="font-mono px-2 py-1 bg-blue-100 dark:bg-blue-900 rounded">
                {isDarkMode ? 'Dark' : 'Light'}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span>System Preference:</span>
              <span className="font-mono px-2 py-1 bg-green-100 dark:bg-green-900 rounded">
                {systemPreference}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span>Following System:</span>
              <span className="font-mono px-2 py-1 bg-yellow-100 dark:bg-yellow-900 rounded">
                {localStorage.getItem('theme') ? 'No' : 'Yes'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col gap-3">
          <button
            onClick={toggleDarkMode}
            className="w-full py-3 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
          >
            Toggle Theme
          </button>
          
          <button
            onClick={resetToSystemPreference}
            className="w-full py-3 px-4 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
          >
            Reset to System Preference
          </button>
        </div>
        
        <div className="text-sm text-gray-500 dark:text-gray-400 mt-8">
          <h3 className="font-semibold mb-2">Testing Instructions:</h3>
          <ol className="list-decimal list-inside space-y-1">
            <li>Check if theme matches your system preference</li>
            <li>Toggle theme manually (should override system)</li>
            <li>Change system theme while manually set (should not change)</li>
            <li>Reset to system preference (should follow system again)</li>
          </ol>
        </div>
      </div>
    </div>
  );
}