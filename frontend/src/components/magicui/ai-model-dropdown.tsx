"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, AlertCircle, Loader2 } from "lucide-react";
import { chatAPI } from "@/lib/api";

// Custom 3D Box Icon Component
const BoxIcon = ({ className }: { className?: string }) => (
  <svg
    width="18"
    height="18"
    viewBox="-1 -1 25 25"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M3.33965 17L11.9999 22L20.6602 17V7L11.9999 2L3.33965 7V17Z"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path
      d="M11.9999 12L3.4999 7M11.9999 12L12 21.5M11.9999 12L20.5 7"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

type AIModel = {
  id: string;
  name: string;
  provider: string;
  description: string;
  features?: string[];
  recommended?: boolean;
};

type Props = {
  selectedModel: string;
  onModelSelect: (modelId: string) => void;
  className?: string;
};

export const AIModelDropdown = ({
  selectedModel,
  onModelSelect,
  className = "",
}: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [aiModels, setAiModels] = useState<AIModel[]>([
    {
      id: "choose-model",
      name: "Choose your model",
      provider: "",
      description: "Select an AI model to use",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch models from enhanced backend
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoading(true);
      setError(null);

      try {
        console.log("🔄 Fetching AI models from backend...");
        const response = await chatAPI.getModels();
        console.log("✅ Models fetched successfully:", response);

        const fetchedModels = response.models || [];

        // Log the fetched models for debugging
        console.log("📋 Fetched models:", fetchedModels);

        // Add the "choose model" option at the beginning
        const modelsWithDefault = [
          {
            id: "choose-model",
            name: "Choose your model",
            provider: "",
            description: "Select an AI model to use",
          },
          ...fetchedModels,
        ];

        setAiModels(modelsWithDefault);
        console.log("📋 Models set in state:", modelsWithDefault);
      } catch (err) {
        console.error("❌ Failed to fetch AI models:", err);
        setError("Failed to load AI models");

        // Fallback to your preferred models only
        const fallbackModels = [
          {
            id: "choose-model",
            name: "Choose your model",
            provider: "",
            description: "Select an AI model to use",
          },
          {
            id: "openai/gpt-oss-120b",
            name: "GPT OSS 120B",
            provider: "OpenAI",
            description: "OpenAI's GPT OSS 120B model for advanced reasoning",
            recommended: true,
          },
          {
            id: "meta-llama/llama-4-maverick-17b-128e-instruct",
            name: "Llama 4 Maverick 17B",
            provider: "Meta",
            description: "Meta's Llama 4 Maverick 17B instruction-tuned model",
          },
          {
            id: "deepseek-r1-distill-llama-70b",
            name: "DeepSeek R1 Distill Llama 70B",
            provider: "DeepSeek",
            description: "DeepSeek's R1 distilled Llama 70B model",
          },
          {
            id: "qwen/qwen3-32b",
            name: "Qwen 3 32B",
            provider: "Alibaba",
            description: "Alibaba's Qwen 3 32B model for multilingual tasks",
          },
          {
            id: "moonshotai/kimi-k2-instruct-0905",
            name: "Kimi K2 Instruct",
            provider: "MoonshotAI",
            description: "MoonshotAI's Kimi K2 instruction-tuned model",
          },
        ];

        setAiModels(fallbackModels);
        console.log("🔄 Using fallback models:", fallbackModels);
      } finally {
        setIsLoading(false);
      }
    };

    fetchModels();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const selectedModelData =
    aiModels.find((model) => model.id === selectedModel) || aiModels[0];

  const refreshModels = async () => {
    setIsLoading(true);
    setError(null);

    try {
      console.log("🔄 Manually refreshing AI models...");
      const response = await chatAPI.getModels();
      console.log("✅ Models refreshed successfully:", response);

      const fetchedModels = response.models || [];

      // Log the fetched models for debugging
      console.log("📋 Refreshed models:", fetchedModels);
      const modelsWithDefault = [
        {
          id: "choose-model",
          name: "Choose your model",
          provider: "",
          description: "Select an AI model to use",
        },
        ...fetchedModels,
      ];

      setAiModels(modelsWithDefault);
      console.log("📋 Models updated in state:", modelsWithDefault);
    } catch (err) {
      console.error("❌ Failed to refresh AI models:", err);
      setError("Failed to refresh AI models");

      // Even on error, we should still show the current models or fallback
      // This ensures the user always sees some options
    } finally {
      setIsLoading(false);
    }
  };

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
        <div className="flex items-center gap-2.5 truncate">
          {isLoading ? (
            <Loader2 className="h-[18px] w-[18px] text-gray-700 dark:text-gray-300 flex-shrink-0 animate-spin" />
          ) : error ? (
            <AlertCircle className="h-[18px] w-[18px] text-red-500 flex-shrink-0" />
          ) : (
            <BoxIcon className="flex-shrink-0 text-gray-700 dark:text-gray-300" />
          )}
          <span className="truncate">
            {error ? "Error loading models" : selectedModelData.name}
          </span>
        </div>
        <div className="flex items-center ml-2">
          <ChevronDown
            className={`h-[18px] w-[18px] text-gray-500 transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 z-50 mt-2 w-72 origin-top-right rounded-2xl bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl border border-gray-200/40 dark:border-gray-700/40 shadow-xl shadow-gray-900/10 dark:shadow-gray-900/30 overflow-hidden">
          <div role="listbox" className="py-2 max-h-80 overflow-y-auto">
            {aiModels.map((model) => (
              <button
                key={model.id}
                type="button"
                className={`w-full px-4 py-2.5 text-left text-sm transition-all duration-150 flex flex-col gap-1 ${
                  selectedModel === model.id
                    ? "bg-blue-500/10 dark:bg-blue-500/15 border-l-4 border-blue-500"
                    : "hover:bg-gray-100/80 dark:hover:bg-gray-700/50"
                }`}
                onClick={() => {
                  if (model.id !== "choose-model") {
                    onModelSelect(model.id);
                  }
                  setIsOpen(false);
                }}
                disabled={model.id === "choose-model"}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {model.name}
                  </span>
                  <div className="flex items-center gap-2">
                    {model.recommended && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 px-2 py-0.5 rounded-full">
                        Recommended
                      </span>
                    )}
                    {selectedModel === model.id && (
                      <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                    )}
                  </div>
                </div>
                {model.provider && (
                  <div className="flex items-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {model.provider}
                    </span>
                    {model.features && model.features.length > 0 && (
                      <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">
                        • {model.features.slice(0, 2).join(", ")}
                      </span>
                    )}
                  </div>
                )}
                {model.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
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
