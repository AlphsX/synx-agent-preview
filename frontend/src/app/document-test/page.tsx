'use client';

import { useState, useEffect } from 'react';

export default function DocumentTest() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    console.log("Applying theme:", isDarkMode);
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      console.log("Added 'dark' class to document");
    } else {
      document.documentElement.classList.remove('dark');
      console.log("Removed 'dark' class from document");
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    console.log("Toggling dark mode from", isDarkMode, "to", !isDarkMode);
    setIsDarkMode(!isDarkMode);
  };

  const checkDarkMode = () => {
    const hasDarkClass = document.documentElement.classList.contains('dark');
    console.log("Document has 'dark' class:", hasDarkClass);
    alert(`Document has 'dark' class: ${hasDarkClass}`);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-50 p-8">
      <h1 className="text-2xl font-bold mb-4">
        Document Test
      </h1>
      <p className="mb-4">
        Current mode: {isDarkMode ? 'Dark' : 'Light'}
      </p>
      
      <div className="space-x-4">
        <button
          onClick={toggleDarkMode}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Toggle Dark Mode
        </button>
        
        <button
          onClick={checkDarkMode}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
        >
          Check Dark Mode
        </button>
      </div>
      
      <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded">
        <p>
          This text should change color when dark mode is toggled.
        </p>
      </div>
    </div>
  );
}