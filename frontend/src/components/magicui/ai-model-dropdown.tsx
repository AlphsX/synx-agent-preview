"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, AlertCircle, Loader2 } from "lucide-react";
import { chatAPI } from "@/lib/api";

// Custom Icon Components based on your specifications
const GPTIcon = ({ className }: { className?: string }) => (
  <svg
    width="18"
    height="18"
    viewBox="-1 -1 25 25"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`stroke-[2] ${className}`}
  >
    <path
      d="M3.33965 17L11.9999 22L20.6602 17V7L11.9999 2L3.33965 7V17Z"
      stroke="currentColor"
    />
    <path
      d="M11.9999 12L3.4999 7M11.9999 12L12 21.5M11.9999 12L20.5 7"
      stroke="currentColor"
    />
  </svg>
);

const LlamaIcon = ({ className }: { className?: string }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`stroke-[2] ${className}`}
  >
    <path
      d="M6.5 12.5L11.5 17.5M6.5 12.5L11.8349 6.83172C13.5356 5.02464 15.9071 4 18.3887 4H20V5.61135C20 8.09292 18.9754 10.4644 17.1683 12.1651L11.5 17.5M6.5 12.5L2 11L5.12132 7.87868C5.68393 7.31607 6.44699 7 7.24264 7H11M11.5 17.5L13 22L16.1213 18.8787C16.6839 18.3161 17 17.553 17 16.7574V13"
      stroke="currentColor"
      strokeLinecap="square"
    />
    <path
      d="M4.5 16.5C4.5 16.5 4 18 4 20C6 20 7.5 19.5 7.5 19.5"
      stroke="currentColor"
    />
  </svg>
);

const DeepSeekIcon = ({ className }: { className?: string }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`stroke-[2] ${className}`}
  >
    <path
      d="M19 9C19 12.866 15.866 17 12 17C8.13398 17 4.99997 12.866 4.99997 9C4.99997 5.13401 8.13398 3 12 3C15.866 3 19 5.13401 19 9Z"
      className="fill-yellow-100 dark:fill-yellow-300 origin-center transition-[transform,opacity] duration-100 scale-0 opacity-0"
    />
    <path
      d="M15 16.1378L14.487 15.2794L14 15.5705V16.1378H15ZM8.99997 16.1378H9.99997V15.5705L9.51293 15.2794L8.99997 16.1378ZM18 9C18 11.4496 16.5421 14.0513 14.487 15.2794L15.5129 16.9963C18.1877 15.3979 20 12.1352 20 9H18ZM12 4C13.7598 4 15.2728 4.48657 16.3238 5.33011C17.3509 6.15455 18 7.36618 18 9H20C20 6.76783 19.082 4.97946 17.5757 3.77039C16.0931 2.58044 14.1061 2 12 2V4ZM5.99997 9C5.99997 7.36618 6.64903 6.15455 7.67617 5.33011C8.72714 4.48657 10.2401 4 12 4V2C9.89382 2 7.90681 2.58044 6.42427 3.77039C4.91791 4.97946 3.99997 6.76783 3.99997 9H5.99997ZM9.51293 15.2794C7.4578 14.0513 5.99997 11.4496 5.99997 9H3.99997C3.99997 12.1352 5.81225 15.3979 8.48701 16.9963L9.51293 15.2794ZM9.99997 19.5001V16.1378H7.99997V19.5001H9.99997ZM10.5 20.0001C10.2238 20.0001 9.99997 19.7763 9.99997 19.5001H7.99997C7.99997 20.8808 9.11926 22.0001 10.5 22.0001V20.0001ZM13.5 20.0001H10.5V22.0001H13.5V20.0001ZM14 19.5001C14 19.7763 13.7761 20.0001 13.5 20.0001V22.0001C14.8807 22.0001 16 20.8808 16 19.5001H14ZM14 16.1378V19.5001H16V16.1378H14Z"
      fill="currentColor"
    />
    <path d="M9 16.0001H15" stroke="currentColor" />
    <path d="M12 16V12" stroke="currentColor" strokeLinecap="square" />
    <g>
      <path
        d="M20 7L19 8"
        stroke="currentColor"
        strokeLinecap="round"
        className="transition-[transform,opacity] duration-100 ease-in-out translate-x-0 translate-y-0 opacity-0"
      />
      <path
        d="M20 9L19 8"
        stroke="currentColor"
        strokeLinecap="round"
        className="transition-[transform,opacity] duration-100 ease-in-out translate-x-0 translate-y-0 opacity-0"
      />
      <path
        d="M4 7L5 8"
        stroke="currentColor"
        strokeLinecap="round"
        className="transition-[transform,opacity] duration-100 ease-in-out translate-x-0 translate-y-0 opacity-0"
      />
      <path
        d="M4 9L5 8"
        stroke="currentColor"
        strokeLinecap="round"
        className="transition-[transform,opacity] duration-100 ease-in-out translate-x-0 translate-y-0 opacity-0"
      />
    </g>
  </svg>
);

const QwenIcon = ({ className }: { className?: string }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`stroke-[2] ${className}`}
  >
    <path
      d="M5 14.25L14 4L13 9.75H19L10 20L11 14.25H5Z"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

const KimiIcon = ({ className }: { className?: string }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`stroke-[2] ${className}`}
  >
    <rect
      x="4"
      y="4"
      width="5"
      height="5"
      stroke="currentColor"
      strokeWidth="2"
    />
    <rect
      x="15"
      y="4"
      width="5"
      height="5"
      stroke="currentColor"
      strokeWidth="2"
    />
    <rect
      x="15"
      y="15"
      width="5"
      height="5"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path
      d="M11 18H10C7.79086 18 6 16.2091 6 14V13"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

// Helper function to get icon and description for each model
const getModelInfo = (modelId: string, modelName: string) => {
  // GPT OSS 120B - Fast and powerful
  if (modelId.includes("gpt-oss")) {
    return {
      icon: <GPTIcon className="h-5 w-5" />,
      shortName: modelName,
      description: "Fast & Accurate",
    };
  }

  // Llama 4 - Balanced performance
  if (modelId.includes("llama-4") || modelId.includes("llama4")) {
    return {
      icon: <LlamaIcon className="h-5 w-5" />,
      shortName: modelName,
      description: "Balanced & Quick",
    };
  }

  // DeepSeek - Deep thinking
  if (modelId.includes("deepseek")) {
    return {
      icon: <DeepSeekIcon className="h-5 w-5" />,
      shortName: modelName,
      description: "Deep Thinking",
    };
  }

  // Qwen - Multilingual expert
  if (modelId.includes("qwen")) {
    return {
      icon: <QwenIcon className="h-5 w-5" />,
      shortName: modelName,
      description: "Multilingual Expert",
    };
  }

  // Kimi - Creative and smart
  if (modelId.includes("kimi")) {
    return {
      icon: <KimiIcon className="h-5 w-5" />,
      shortName: modelName,
      description: "Creative & Smart",
    };
  }

  // Default
  return {
    icon: <GPTIcon className="h-5 w-5" />,
    shortName: modelName,
    description: "AI Model",
  };
};

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

  const selectedModelInfo = getModelInfo(
    selectedModelData.id,
    selectedModelData.name
  );

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Dropdown Button */}
      <button
        type="button"
        className="flex items-center justify-between w-full rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm font-medium transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-700/80 text-gray-900 dark:text-gray-100"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2 truncate">
          {isLoading ? (
            <Loader2 className="h-[18px] w-[18px] flex-shrink-0 animate-spin" />
          ) : error ? (
            <AlertCircle className="h-[18px] w-[18px] text-red-500 flex-shrink-0" />
          ) : (
            <span className="flex-shrink-0">{selectedModelInfo.icon}</span>
          )}
          <span className="truncate font-medium">
            {error ? "Error loading models" : selectedModelData.name}
          </span>
        </div>
        <ChevronDown
          className={`h-4 w-4 text-gray-500 transition-transform duration-200 flex-shrink-0 ml-2 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 right-0 md:left-auto md:right-0 md:w-80 z-50 mt-2 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg overflow-hidden animate-dropdown-in">
          <div
            role="listbox"
            className="py-1 max-h-[60vh] md:max-h-96 overflow-y-auto"
          >
            {aiModels.map((model) => {
              if (model.id === "choose-model") return null; // Skip the placeholder

              const modelInfo = getModelInfo(model.id, model.name);
              const isSelected = selectedModel === model.id;

              return (
                <button
                  key={model.id}
                  type="button"
                  className={`w-full px-4 py-3 text-left transition-colors duration-150 flex items-start gap-3 ${
                    isSelected
                      ? "bg-gray-100 dark:bg-gray-700"
                      : "hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  }`}
                  onClick={() => {
                    onModelSelect(model.id);
                    setIsOpen(false);
                  }}
                >
                  {/* Icon */}
                  <div
                    className={`flex-shrink-0 mt-0.5 ${
                      isSelected
                        ? "text-blue-600 dark:text-blue-400"
                        : "text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {modelInfo.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`font-medium text-sm ${
                          isSelected
                            ? "text-gray-900 dark:text-gray-100"
                            : "text-gray-900 dark:text-gray-100"
                        }`}
                      >
                        {model.name}
                      </span>
                      {model.recommended && (
                        <span className="text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-md font-medium flex-shrink-0">
                          Popular
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {modelInfo.description}
                    </p>
                  </div>

                  {/* Selected indicator */}
                  {isSelected && (
                    <div className="flex-shrink-0 mt-1">
                      <div className="h-2 w-2 rounded-full bg-blue-600 dark:bg-blue-400"></div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
