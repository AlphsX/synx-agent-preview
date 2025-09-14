'use client';

import { useState } from 'react';

export default function ToggleTest() {
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">Sidebar Toggle Test</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Testing Instructions</h2>
          <ul className="list-disc pl-5 space-y-2 text-gray-700 dark:text-gray-300">
            <li>Click anywhere on the sidebar to toggle its visibility</li>
            <li>Click on buttons/interactive elements to verify they still work</li>
            <li>Check that the cursor changes appropriately (left arrow when expanded, right arrow when collapsed)</li>
          </ul>
        </div>

        {/* Desktop Sidebar - Test Implementation */}
        <div className="flex">
          <div 
            className={`bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-col transition-all duration-300 
              ${isDesktopSidebarCollapsed ? 'w-16 cursor-e-resize' : 'w-64 cursor-w-resize'} overflow-hidden`}
            onClick={(e) => {
              // Prevent toggle when clicking on interactive elements
              const target = e.target as HTMLElement;
              const isInteractiveElement = target.closest('button, a, input, textarea, select');
              
              if (!isInteractiveElement) {
                e.stopPropagation();
                setIsDesktopSidebarCollapsed(prev => !prev);
              }
            }}
          >
            {/* Sidebar Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {isDesktopSidebarCollapsed ? 'Menu' : 'Navigation'}
              </h2>
            </div>

            {/* Sidebar Content */}
            <div className="p-4">
              {!isDesktopSidebarCollapsed ? (
                <div className="space-y-4">
                  <button 
                    className="w-full text-left p-3 rounded-lg bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert('Profile button clicked!');
                    }}
                  >
                    Profile
                  </button>
                  <button 
                    className="w-full text-left p-3 rounded-lg bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert('Settings button clicked!');
                    }}
                  >
                    Settings
                  </button>
                  <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      This is a non-interactive area. Clicking here should toggle the sidebar.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 flex flex-col items-center">
                  <button 
                    className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 flex items-center justify-center hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                    title="Profile"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert('Profile button clicked!');
                    }}
                  >
                    P
                  </button>
                  <button 
                    className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 flex items-center justify-center hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                    title="Settings"
                    onClick={(e) => {
                      e.stopPropagation();
                      alert('Settings button clicked!');
                    }}
                  >
                    S
                  </button>
                </div>
              )}
            </div>

            {/* Sidebar Footer */}
            <div className="p-4 mt-auto border-t border-gray-200 dark:border-gray-700">
              <button 
                className="w-full p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsDesktopSidebarCollapsed(!isDesktopSidebarCollapsed);
                }}
              >
                {isDesktopSidebarCollapsed ? '→' : '←'}
              </button>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Main Content Area</h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                This is the main content area. The sidebar on the left can be toggled by clicking anywhere on it,
                except on interactive elements like buttons.
              </p>
              <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Current State:</h3>
                <p className="text-gray-700 dark:text-gray-300">
                  Sidebar is <span className="font-semibold">{isDesktopSidebarCollapsed ? 'collapsed' : 'expanded'}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}