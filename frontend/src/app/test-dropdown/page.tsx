'use client';

import { useState } from 'react';
import { AIModelDropdown } from '@/components/magicui/ai-model-dropdown';

export default function TestDropdown() {
  const [selectedModel, setSelectedModel] = useState('openai/gpt-oss-120b');
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">AI Model Dropdown Test</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Current Selection</h2>
          <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <p className="text-gray-700 dark:text-gray-300">
              <span className="font-medium">Selected Model:</span> {selectedModel}
            </p>
          </div>
          
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Dropdown Component</h2>
          <div className="flex justify-end">
            <AIModelDropdown 
              selectedModel={selectedModel}
              onModelSelect={setSelectedModel}
            />
          </div>
        </div>
        
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Instructions</h2>
          <ul className="list-disc pl-5 space-y-2 text-gray-600 dark:text-gray-400">
            <li>Click the dropdown to see the list of AI models</li>
            <li>Select any model to update the current selection</li>
            <li>The dropdown should show a luxurious, modern design</li>
            <li>Each model should display its name, provider, and description</li>
          </ul>
        </div>
      </div>
    </div>
  );
}