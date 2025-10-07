"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Plus, Globe, TrendingUp, Sparkles, AlertCircle, Loader2, Search, Newspaper } from "lucide-react";
import { chatAPI } from "@/lib/api";

type SearchTool = {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  hoverBgColor: string;
  available: boolean;
  providers?: string[];
  primary_provider?: string;
};

type Props = {
  onToolSelect: (toolId: string) => void;
  selectedTool: string | null;
  isDarkMode: boolean;
  className?: string;
  onDropdownStateChange?: (isOpen: boolean) => void;
};

const getIconForTool = (toolId: string) => {
  switch (toolId) {
    case 'web_search':
      return <Globe className="h-5 w-5" />;
    case 'news_search':
      return <Newspaper className="h-5 w-5" />;
    case 'crypto_data':
      return <TrendingUp className="h-5 w-5" />;
    case 'vector_search':
      return <Search className="h-5 w-5" />;
    default:
      return <Sparkles className="h-5 w-5" />;
  }
};

const getColorForTool = (toolId: string) => {
  switch (toolId) {
    case 'web_search':
      return {
        color: 'text-blue-500',
        bgColor: 'bg-blue-500/10',
        hoverBgColor: 'hover:bg-blue-500/10'
      };
    case 'news_search':
      return {
        color: 'text-orange-500',
        bgColor: 'bg-orange-500/10',
        hoverBgColor: 'hover:bg-orange-500/10'
      };
    case 'crypto_data':
      return {
        color: 'text-green-500',
        bgColor: 'bg-green-500/10',
        hoverBgColor: 'hover:bg-green-500/10'
      };
    case 'vector_search':
      return {
        color: 'text-purple-500',
        bgColor: 'bg-purple-500/10',
        hoverBgColor: 'hover:bg-purple-500/10'
      };
    default:
      return {
        color: 'text-gray-500',
        bgColor: 'bg-gray-500/10',
        hoverBgColor: 'hover:bg-gray-500/10'
      };
  }
};

export const SearchToolsDropdown = ({ onToolSelect, selectedTool, isDarkMode, className = "", onDropdownStateChange }: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);
  const [searchTools, setSearchTools] = useState<SearchTool[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const plusButtonRef = useRef<HTMLButtonElement>(null);
  
  // Fetch search tools from enhanced backend
  useEffect(() => {
    const fetchSearchTools = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await chatAPI.getSearchTools();
        const fetchedTools = response.tools || [];
        
        // Transform backend tools to frontend format
        const transformedTools: SearchTool[] = fetchedTools.map((tool: any) => {
          const colors = getColorForTool(tool.id);
          return {
            id: tool.id,
            name: tool.name,
            description: tool.description,
            icon: getIconForTool(tool.id),
            available: tool.available,
            providers: tool.providers,
            primary_provider: tool.primary_provider,
            ...colors
          };
        });
        
        setSearchTools(transformedTools);
      } catch (err) {
        console.error('Failed to fetch search tools:', err);
        setError('Failed to load search tools');
        
        // Fallback to default tools if API fails - enhanced with news search
        setSearchTools([
          { 
            id: 'web_search', 
            name: 'Search web', 
            description: 'Search the web for current information',
            icon: <Globe className="h-5 w-5" />, 
            color: 'text-blue-500',
            bgColor: 'bg-blue-500/10',
            hoverBgColor: 'hover:bg-blue-500/10',
            available: true,
            providers: ['SerpAPI', 'Brave Search'],
            primary_provider: 'SerpAPI'
          },
          { 
            id: 'news_search', 
            name: 'Search news', 
            description: 'Search for latest news and current events',
            icon: <Newspaper className="h-5 w-5" />, 
            color: 'text-orange-500',
            bgColor: 'bg-orange-500/10',
            hoverBgColor: 'hover:bg-orange-500/10',
            available: true,
            providers: ['SerpAPI', 'Brave Search'],
            primary_provider: 'SerpAPI'
          },
          { 
            id: 'crypto_data', 
            name: 'Get crypto data', 
            description: 'Get real-time cryptocurrency market data',
            icon: <TrendingUp className="h-5 w-5" />, 
            color: 'text-green-500',
            bgColor: 'bg-green-500/10',
            hoverBgColor: 'hover:bg-green-500/10',
            available: true,
            providers: ['Binance'],
            primary_provider: 'Binance'
          },
          { 
            id: 'vector_search', 
            name: 'Knowledge Search', 
            description: 'Search domain-specific knowledge base',
            icon: <Search className="h-5 w-5" />, 
            color: 'text-purple-500',
            bgColor: 'bg-purple-500/10',
            hoverBgColor: 'hover:bg-purple-500/10',
            available: true,
            providers: ['Vector Database'],
            primary_provider: 'PostgreSQL + pgvector'
          }
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSearchTools();
  }, []);

  // Handle tool selection
  const handleToolSelect = useCallback((toolId: string) => {
    onToolSelect(toolId);
    setIsOpen(false);
    setHighlightedIndex(-1);
  }, [onToolSelect]);

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
  }, [isOpen, highlightedIndex, searchTools, handleToolSelect]);
  
  // Focus management
  useEffect(() => {
    if (isOpen) {
      setHighlightedIndex(0); // Highlight first item by default
    } else {
      setHighlightedIndex(-1); // Reset highlight when closed
    }
  }, [isOpen]);

  // Notify parent component about dropdown state changes
  useEffect(() => {
    onDropdownStateChange?.(isOpen);
  }, [isOpen, onDropdownStateChange]);
  
  // Calculate the button color based on selected tool
  const getButtonColor = () => {
    if (selectedTool === 'web_search') return '#3b82f6';
    if (selectedTool === 'news_search') return '#f97316';
    if (selectedTool === 'crypto_data') return '#10b981';
    if (selectedTool === 'vector_search') return '#8b5cf6';
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
        disabled={isLoading}
        data-plus-button
      >
        {isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : error ? (
          <AlertCircle className="h-5 w-5" />
        ) : (
          <Plus className="h-5 w-5" />
        )}
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
            {error ? 'Error Loading Tools' : 'Select Tools'}
          </div>
          {error ? (
            <div className="px-4 py-3 text-sm text-red-600 dark:text-red-400 flex items-center">
              <AlertCircle className="h-4 w-4 mr-2" />
              <span>Failed to load search tools</span>
            </div>
          ) : (
            searchTools.map((tool, index) => (
              <button
                key={tool.id}
                type="button"
                className={`w-full px-4 py-3 text-left text-sm transition-all duration-200 group rounded-xl mx-1 ${
                  tool.available 
                    ? `text-gray-700 dark:text-gray-300 hover:${tool.bgColor} dark:hover:${tool.bgColor}` 
                    : 'text-gray-400 dark:text-gray-600 cursor-not-allowed opacity-60'
                } ${highlightedIndex === index ? `${tool.bgColor} dark:${tool.bgColor}` : ''}`}
                onClick={() => tool.available && handleToolSelect(tool.id)}
                disabled={!tool.available}
              >
                <div className="flex items-start">
                  <div className={`${tool.available ? tool.color : 'text-gray-400 dark:text-gray-600'} mr-3 group-hover:scale-110 transition-transform duration-200 flex-shrink-0 mt-0.5`}>
                    {tool.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="group-hover:translate-x-1 transition-transform duration-200 font-medium truncate">
                        {tool.name}
                      </span>
                      {!tool.available && (
                        <span className="text-xs text-red-500 dark:text-red-400 ml-2 flex-shrink-0">
                          Unavailable
                        </span>
                      )}
                    </div>
                    {tool.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                        {tool.description}
                      </p>
                    )}
                    {tool.primary_provider && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        via {tool.primary_provider}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};