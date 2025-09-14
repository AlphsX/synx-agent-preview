'use client';

import { useDarkMode } from '@/hooks/useDarkMode';

export default function MinimalTest() {
  const { isDarkMode, toggleDarkMode, resetToSystemPreference } = useDarkMode();
  
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <h1 className="text-3xl font-bold mb-8">Minimal Theme Test</h1>
      
      <div className="mb-8 p-6 rounded-xl bg-gray-100 dark:bg-gray-800 shadow-lg">
        <p className="text-lg">Dark Mode: {isDarkMode ? 'enabled' : 'disabled'}</p>
        <p className="text-lg">System Preference: {typeof window !== 'undefined' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : 'unknown'}</p>
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
          Reset to System
        </button>
      </div>
    </div>
  );
}