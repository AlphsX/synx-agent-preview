"use client";

import { useDarkMode } from '@/hooks/useDarkMode';
import { useDynamicFavicon } from '@/hooks/useDynamicFavicon';
import { AnimatedThemeToggler } from '@/components/magicui/animated-theme-toggler';

export default function FaviconTest() {
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
            Dynamic Favicon Test
          </h1>
          
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <div className="text-yellow-600 dark:text-yellow-400 text-xl">💡</div>
              <div>
                <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                  How to Test
                </h3>
                <p className="text-yellow-700 dark:text-yellow-300 text-sm">
                  Look at your browser tab! The favicon should change between light and dark versions when you toggle the theme.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Theme Controls
            </h2>
            <div className="flex items-center gap-4 mb-4">
              <AnimatedThemeToggler
                isDarkMode={isDarkMode}
                toggleDarkMode={toggleDarkMode}
                isUsingSystemPreference={isUsingSystemPreference}
                className="p-3 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
              />
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Click to toggle theme and watch the favicon change!
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Current Status
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Theme:</span>
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
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">System Pref:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {systemPreference ? 'Dark' : 'Light'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Favicon:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {isDarkMode ? 'icon-dark.png' : 'icon-light.png'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Test Scenarios
            </h2>
            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-start gap-2">
                <span className="text-green-500 font-bold">✓</span>
                <span>Toggle theme manually - favicon should change instantly</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-500 font-bold">✓</span>
                <span>Change system theme in OS - favicon should follow (if using system mode)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-500 font-bold">✓</span>
                <span>Refresh page - favicon should match current theme immediately</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-500 font-bold">✓</span>
                <span>Open in new tab - favicon should be correct from the start</span>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="text-blue-600 dark:text-blue-400 text-xl">ℹ️</div>
              <div>
                <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-1">
                  Technical Details
                </h3>
                <ul className="text-blue-700 dark:text-blue-300 text-sm space-y-1">
                  <li>• Favicon changes are handled by useDynamicFavicon hook</li>
                  <li>• Initial favicon is set in layout.tsx with inline script</li>
                  <li>• Works with both manual and system theme preferences</li>
                  <li>• SSR-safe and prevents favicon flashing</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}