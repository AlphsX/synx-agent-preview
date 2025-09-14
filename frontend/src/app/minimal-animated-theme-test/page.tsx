'use client';

import { useState, useEffect } from 'react';
import { Moon, SunDim } from 'lucide-react';

const AnimatedThemeToggler = ({ isDarkMode, toggleDarkMode, className }: { isDarkMode: boolean; toggleDarkMode: () => void; className?: string }) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    console.log("AnimatedThemeToggler clicked!");
    console.log("Current isDarkMode value:", isDarkMode);
    e.stopPropagation();
    e.preventDefault();
    toggleDarkMode();
    console.log("toggleDarkMode called");
  };

  return (
    <button 
      onClick={handleClick} 
      className={`${className} transition-transform duration-200 active:scale-95`}
      aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDarkMode ? <SunDim size={20} /> : <Moon size={20} />}
    </button>
  );
};

export default function MinimalAnimatedThemeTest() {
  const [isDarkMode, setIsDarkMode] = useState(true);

  useEffect(() => {
    console.log("Applying theme:", isDarkMode);
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    console.log("Toggling dark mode from", isDarkMode, "to", !isDarkMode);
    setIsDarkMode(!isDarkMode);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 p-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        Minimal Animated Theme Test
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