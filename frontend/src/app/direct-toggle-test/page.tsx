'use client';

import { useState, useEffect } from 'react';
import { AnimatedThemeToggler } from '@/components/magicui';

export default function DirectToggleTest() {
  const [isDarkMode, setIsDarkMode] = useState(true);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-1000 dark:via-gray-950 dark:to-gray-900 text-gray-900 dark:text-gray-50 p-8">
      <h1 className="text-2xl font-bold mb-4">
        Direct Toggle Test
      </h1>
      <p className="mb-4">
        Current mode: {isDarkMode ? 'Dark' : 'Light'}
      </p>
      
      <div className="mb-4">
        <AnimatedThemeToggler 
          isDarkMode={isDarkMode}
          toggleDarkMode={toggleDarkMode}
          className="p-4 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
        />
      </div>
      
      <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded">
        <p>
          This text should change color when dark mode is toggled.
        </p>
      </div>
    </div>
  );
}