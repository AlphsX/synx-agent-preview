'use client';

import { useDarkMode } from '@/hooks/useDarkMode';
import { AnimatedThemeToggler } from '@/components/magicui';

export default function AnimatedThemeTest() {
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 p-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        Animated Theme Toggler Test
      </h1>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
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
        <p className="text-gray-800 dark:text-gray-200">
          This text should change color when dark mode is toggled.
        </p>
      </div>
    </div>
  );
}