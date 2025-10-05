"use client";

import { Moon, Sun, Monitor } from "lucide-react";
import { useState, useRef, useEffect } from "react";

type Props = {
  isDarkMode: boolean;
  isUsingSystemPreference: boolean;
  systemPreference: boolean;
  toggleDarkMode: () => void;
  resetToSystemPreference: () => void;
  className?: string;
};

export const EnhancedThemeToggler = ({ 
  isDarkMode, 
  isUsingSystemPreference,
  systemPreference,
  toggleDarkMode, 
  resetToSystemPreference,
  className 
}: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSystemMode = () => {
    resetToSystemPreference();
    setIsOpen(false);
  };

  const handleLightMode = () => {
    if (isDarkMode) toggleDarkMode();
    setIsOpen(false);
  };

  const handleDarkMode = () => {
    if (!isDarkMode) toggleDarkMode();
    setIsOpen(false);
  };

  const getCurrentIcon = () => {
    if (isUsingSystemPreference) {
      return <Monitor size={20} />;
    }
    return isDarkMode ? <Moon size={20} /> : <Sun size={20} />;
  };

  const getCurrentLabel = () => {
    if (isUsingSystemPreference) {
      return `System (${systemPreference ? 'Dark' : 'Light'})`;
    }
    return isDarkMode ? 'Dark' : 'Light';
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
        aria-label="Theme selector"
      >
        <div className="transition-all duration-300 ease-out">
          {getCurrentIcon()}
        </div>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {getCurrentLabel()}
        </span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="py-1">
            <button
              onClick={handleSystemMode}
              className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                isUsingSystemPreference ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Monitor size={16} />
              <span>System</span>
              {isUsingSystemPreference && (
                <div className="ml-auto w-2 h-2 bg-blue-500 rounded-full"></div>
              )}
            </button>
            <button
              onClick={handleLightMode}
              className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                !isUsingSystemPreference && !isDarkMode ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Sun size={16} />
              <span>Light</span>
              {!isUsingSystemPreference && !isDarkMode && (
                <div className="ml-auto w-2 h-2 bg-blue-500 rounded-full"></div>
              )}
            </button>
            <button
              onClick={handleDarkMode}
              className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                !isUsingSystemPreference && isDarkMode ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Moon size={16} />
              <span>Dark</span>
              {!isUsingSystemPreference && isDarkMode && (
                <div className="ml-auto w-2 h-2 bg-blue-500 rounded-full"></div>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};