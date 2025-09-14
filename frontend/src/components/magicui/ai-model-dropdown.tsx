"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Zap } from "lucide-react";

type AIModel = {
  id: string;
  name: string;
  provider: string;
  description: string;
};

type Props = {
  selectedModel: string;
  onModelSelect: (modelId: string) => void;
  className?: string;
};

const aiModels: AIModel[] = [
  { id: 'choose-model', name: 'Choose your model', provider: '', description: 'Select an AI model to use' },
  { id: 'openai/gpt-oss-120b', name: 'GPT-OSS-120B', provider: 'OpenAI', description: 'Open source 120B parameter model' },
  { id: 'meta-llama/llama-4-maverick-17b-128e-instruct', name: 'Llama-4 Maverick 17B', provider: 'Meta', description: '17B parameter model with 128 experts' },
  { id: 'deepseek-r1-distill-llama-70b', name: 'DeepSeek R1 Distill Llama 70B', provider: 'DeepSeek', description: 'Distilled version of DeepSeek R1 with 70B parameters' },
  { id: 'qwen/qwen3-32b', name: 'Qwen3 32B', provider: 'Qwen', description: 'Latest Qwen model with 32B parameters' },
  { id: 'moonshotai/kimi-k2-instruct', name: 'Kimi K2 Instruct', provider: 'Moonshot AI', description: 'Kimi K2 instruction-following model' }
];

export const AIModelDropdown = ({ selectedModel, onModelSelect, className = "" }: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);
  
  const selectedModelData = aiModels.find(model => model.id === selectedModel) || aiModels[0];
  
  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Dropdown Button */}
      <button
        type="button"
        className="flex items-center justify-between w-full rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border border-gray-200/40 dark:border-gray-700/40 px-4 py-2.5 text-sm font-medium transition-all duration-200 shadow hover:shadow-md text-gray-700 dark:text-gray-300 hover:bg-white/90 dark:hover:bg-gray-700/90"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex items-center truncate">
          <Zap className="h-4 w-4 mr-2 text-blue-500 flex-shrink-0" />
          <span className="truncate">{selectedModelData.name}</span>
        </div>
        <ChevronDown 
          className={`h-4 w-4 ml-2 text-gray-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>
      
      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 z-50 mt-2 w-72 origin-top-right rounded-2xl bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl border border-gray-200/40 dark:border-gray-700/40 shadow-xl shadow-gray-900/10 dark:shadow-gray-900/30 overflow-hidden">
          <div 
            role="listbox"
            className="py-2 max-h-80 overflow-y-auto"
          >
            {aiModels.map((model) => (
              <button
                key={model.id}
                type="button"
                className={`w-full px-4 py-3 text-left text-sm transition-all duration-150 flex flex-col ${
                  selectedModel === model.id 
                    ? 'bg-blue-500/10 dark:bg-blue-500/15 border-l-4 border-blue-500' 
                    : 'hover:bg-gray-100/80 dark:hover:bg-gray-700/50'
                }`}
                onClick={() => {
                  if (model.id !== 'choose-model') {
                    onModelSelect(model.id);
                  }
                  setIsOpen(false);
                }}
                disabled={model.id === 'choose-model'}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {model.name}
                  </span>
                  {selectedModel === model.id && (
                    <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                  )}
                </div>
                {model.provider && (
                  <div className="flex items-center mt-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {model.provider}
                    </span>
                  </div>
                )}
                {model.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                    {model.description}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};