'use client';

import { useState } from 'react';
import { SearchToolsDropdown } from '@/components/magicui/search-tools-dropdown';
import { useDarkMode } from '@/hooks';

export default function TestSearchTools() {
  const { isDarkMode } = useDarkMode();
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const handleToolSelect = (toolId: string) => {
    setSelectedTool(toolId);
    setLogs(prev => [...prev, `Selected tool: ${toolId} at ${new Date().toLocaleTimeString()}`]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">Search Tools Dropdown Test</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Component Demo</h2>
          <div className="flex justify-center py-8">
            <SearchToolsDropdown 
              onToolSelect={handleToolSelect}
              selectedTool={selectedTool}
              isDarkMode={isDarkMode}
            />
          </div>
          
          <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <p className="text-gray-700 dark:text-gray-300">
              <span className="font-medium">Selected Tool:</span> {selectedTool || 'None'}
            </p>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Event Logs</h2>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} className="p-2 bg-gray-50 dark:bg-gray-700 rounded text-sm text-gray-600 dark:text-gray-400">
                  {log}
                </div>
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400 italic">No events yet. Click on a tool to see logs here.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}