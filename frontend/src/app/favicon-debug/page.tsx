"use client";

import { useDarkMode } from "@/hooks/useDarkMode";
import { useDynamicFavicon } from "@/hooks/useDynamicFavicon";
import { useState, useEffect } from "react";

export default function FaviconDebugPage() {
  const {
    isDarkMode,
    toggleDarkMode,
    resetToSystemPreference,
    isUsingSystemPreference,
    systemPreference,
    isHydrated,
  } = useDarkMode();

  // Dynamic favicon based on theme
  useDynamicFavicon(isDarkMode);

  const [currentFaviconHref, setCurrentFaviconHref] = useState<string>("");

  useEffect(() => {
    // Monitor favicon changes
    const updateFaviconInfo = () => {
      const faviconLink = document.getElementById("favicon") as HTMLLinkElement;
      if (faviconLink) {
        setCurrentFaviconHref(faviconLink.href);
      }
    };

    updateFaviconInfo();

    // Check every 500ms for changes
    const interval = setInterval(updateFaviconInfo, 500);

    return () => clearInterval(interval);
  }, [isDarkMode]);

  if (!isHydrated) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-black dark:text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Favicon Debug Page</h1>

        <div className="grid gap-6">
          {/* Current Status */}
          <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Current Status</h2>
            <div className="space-y-2 text-sm">
              <div>
                <strong>App Theme:</strong> {isDarkMode ? "Dark" : "Light"}
              </div>
              <div>
                <strong>System Preference:</strong>{" "}
                {systemPreference ? "Dark" : "Light"}
              </div>
              <div>
                <strong>Using System Preference:</strong>{" "}
                {isUsingSystemPreference ? "Yes" : "No"}
              </div>
              <div>
                <strong>Is Hydrated:</strong> {isHydrated ? "Yes" : "No"}
              </div>
            </div>
          </div>

          {/* Favicon Info */}
          <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Favicon Information</h2>
            <div className="space-y-2 text-sm">
              <div>
                <strong>Current Favicon URL:</strong>
                <div className="mt-1 p-2 bg-gray-200 dark:bg-gray-700 rounded text-xs break-all">
                  {currentFaviconHref || "Not found"}
                </div>
              </div>
              <div>
                <strong>Expected Color:</strong>{" "}
                {isDarkMode ? "White (#ffffff)" : "Black (#000000)"}
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Theme Controls</h2>
            <div className="space-y-4">
              <button
                onClick={toggleDarkMode}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                Toggle Theme (Currently: {isDarkMode ? "Dark" : "Light"})
              </button>

              <button
                onClick={resetToSystemPreference}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors ml-4"
              >
                Reset to System Preference
              </button>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4 text-yellow-800 dark:text-yellow-200">
              Testing Instructions
            </h2>
            <div className="space-y-2 text-sm text-yellow-700 dark:text-yellow-300">
              <div>
                1. Look at your browser tab - the favicon should match the
                current theme
              </div>
              <div>
                2. Click &quot;Toggle Theme&quot; - favicon should change
                immediately
              </div>
              <div>
                3. Change your system theme in OS settings - if using system
                preference, favicon should follow
              </div>
              <div>
                4. Refresh the page - favicon should match the theme immediately
                on load
              </div>
            </div>
          </div>

          {/* Debug Console */}
          <div className="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Debug Console</h2>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Check your browser&apos;s developer console for favicon update
              logs.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
