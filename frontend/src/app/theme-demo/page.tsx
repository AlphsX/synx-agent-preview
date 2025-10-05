"use client";

import { useDarkMode } from '@/hooks/useDarkMode';
import { useDynamicFavicon } from '@/hooks/useDynamicFavicon';
import { AnimatedThemeToggler } from '@/components/magicui/animated-theme-toggler';

export default function ThemeDemo() {
  const { 
    isDarkMode, 
    toggleDarkMode, 
    isUsingSystemPreference,
    systemPreference,
    isHydrated 
  } = useDarkMode();

  // Dynamic favicon based on theme
  useDynamicFavicon(isDarkMode);

  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 transition-colors duration-300">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
            System-Aware Theme Demo
          </h1>
          
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Theme Toggle Button
            </h2>
            <div className="flex items-center gap-4">
              <AnimatedThemeToggler
                isDarkMode={isDarkMode}
                toggleDarkMode={toggleDarkMode}
                isUsingSystemPreference={isUsingSystemPreference}
                className="p-3 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
              />
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {isUsingSystemPreference 
                  ? `Following system (${systemPreference ? 'Dark' : 'Light'})` 
                  : `Manual override (${isDarkMode ? 'Dark' : 'Light'})`
                }
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Current Status
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Current Theme:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {isDarkMode ? 'Dark' : 'Light'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Using System:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {isUsingSystemPreference ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">System Preference:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {systemPreference ? 'Dark' : 'Light'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Dynamic Favicon
            </h2>
            <div className="text-gray-600 dark:text-gray-400 space-y-2 text-sm">
              <p>• Favicon automatically changes based on current theme</p>
              <p>• Light mode: Uses icon-light.png</p>
              <p>• Dark mode: Uses icon-dark.png</p>
              <p>• Changes instantly when theme switches</p>
              <p>• Check your browser tab to see the favicon change!</p>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              How it works
            </h2>
            <div className="text-gray-600 dark:text-gray-400 space-y-2 text-sm">
              <p>• Theme now defaults to your system preference automatically</p>
              <p>• The toggle button shows a monitor icon when using system preference</p>
              <p>• Clicking the button switches to manual mode (sun/moon icons)</p>
              <p>• Manual selections override system preference until reset</p>
              <p>• Changes to system theme are automatically detected and applied</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}