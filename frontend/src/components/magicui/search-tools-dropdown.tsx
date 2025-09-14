"use client";

import { useState, useRef, useEffect } from "react";
import { Plus, Globe, TrendingUp, Sparkles } from "lucide-react";

type SearchTool = {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  hoverBgColor: string;
};

type Props = {
  onToolSelect: (toolId: string) => void;
  selectedTool: string | null;
  isDarkMode: boolean;
  className?: string;
};

const searchTools: SearchTool[] = [
  { 
    id: 'web', 
    name: 'Search web', 
    icon: <Globe className="h-5 w-5" />, 
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    hoverBgColor: 'hover:bg-blue-500/10'
  },
  { 
    id: 'crypto', 
    name: 'Get crypto data', 
    icon: <TrendingUp className="h-5 w-5" />, 
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    hoverBgColor: 'hover:bg-green-500/10'
  },
  { 
    id: 'ai', 
    name: 'AI Chat', 
    icon: <Sparkles className="h-5 w-5" />, 
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    hoverBgColor: 'hover:bg-purple-500/10'
  }
];

export const SearchToolsDropdown = ({ onToolSelect, selectedTool, isDarkMode, className = "" }: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const plusButtonRef = useRef<HTMLButtonElement>(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          plusButtonRef.current && !plusButtonRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);
  
  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedIndex(prev => prev <= 0 ? searchTools.length - 1 : prev - 1);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedIndex(prev => prev >= searchTools.length - 1 ? 0 : prev + 1);
      } else if (e.key === 'Enter' && highlightedIndex >= 0) {
        e.preventDefault();
        handleToolSelect(searchTools[highlightedIndex].id);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, highlightedIndex]);
  
  // Focus management
  useEffect(() => {
    if (isOpen) {
      setHighlightedIndex(0); // Highlight first item by default
    } else {
      setHighlightedIndex(-1); // Reset highlight when closed
    }
  }, [isOpen]);
  
  const handleToolSelect = (toolId: string) => {
    onToolSelect(toolId);
    setIsOpen(false);
    setHighlightedIndex(-1);
  };
  
  // Calculate the button color
  const getButtonColor = () => {
    if (selectedTool === 'web') return '#3b82f6';
    if (selectedTool === 'crypto') return '#10b981';
    if (selectedTool === 'ai') return '#8b5cf6';
    return isDarkMode ? '#9ca3af' : '#6b7280';
  };
  
  return (
    <div className={`relative ${className}`}>
      {/* Plus Button */}
      <button
        ref={plusButtonRef}
        type="button"
        className={`flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full transition-all duration-200 ease-in-out transform ${
          isOpen ? 'rotate-45' : 'rotate-0'
        } hover:bg-gray-100 dark:hover:bg-gray-700`}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          color: getButtonColor()
        }}
      >
        <Plus className="h-5 w-5" />
      </button>
      
      {/* Dropdown Menu */}
      {isOpen && (
        <div 
          ref={dropdownRef}
          className="absolute bottom-full mb-2 w-48 rounded-2xl shadow-lg border border-gray-200/40 dark:border-gray-700/40 py-2 z-10 bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl animate-fadeInUp"
          style={{ 
            left: '0',
            bottom: 'calc(100% + 0.5rem)',
            animationDuration: '0.3s'
          }}
        >
          <div className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Select Tools
          </div>
          {searchTools.map((tool, index) => (
            <button
              key={tool.id}
              type="button"
              className={`w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:${tool.bgColor} dark:hover:${tool.bgColor} flex items-center transition-all duration-200 group rounded-xl mx-1`}
              onClick={() => handleToolSelect(tool.id)}
            >
              <div className={`${tool.color} mr-3 group-hover:scale-110 transition-transform duration-200`}>
                {tool.icon}
              </div>
              <span className="group-hover:translate-x-1 transition-transform duration-200 font-medium">
                {tool.name}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};