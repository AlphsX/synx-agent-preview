"use client";

import { useEffect, useState } from "react";

interface LoadingScreenProps {
  isLoading: boolean;
  onLoadingComplete?: () => void;
}

export function LoadingScreen({
  isLoading,
  onLoadingComplete,
}: LoadingScreenProps) {
  const [progress, setProgress] = useState(0);
  const [isExiting, setIsExiting] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Handle hydration and mobile viewport
  useEffect(() => {
    setIsHydrated(true);

    // Set up proper mobile viewport height
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty("--vh", `${vh}px`);
    };

    setVH();
    window.addEventListener("resize", setVH);
    window.addEventListener("orientationchange", setVH);

    return () => {
      window.removeEventListener("resize", setVH);
      window.removeEventListener("orientationchange", setVH);
    };
  }, []);

  useEffect(() => {
    if (!isLoading || !isHydrated) return;

    let startTime: number;
    const duration = 800; // Match the useAppLoading duration
    let animationId: number;

    const updateProgress = (timestamp: number) => {
      if (!startTime) startTime = timestamp;

      const elapsed = timestamp - startTime;
      const rawProgress = (elapsed / duration) * 100;

      // Smooth easing curve (ease-out)
      const easedProgress = 100 * (1 - Math.pow(1 - rawProgress / 100, 3));

      setProgress(Math.min(easedProgress, 100));

      if (rawProgress < 100) {
        animationId = requestAnimationFrame(updateProgress);
      } else {
        // Start exit animation
        setIsExiting(true);
        setTimeout(() => onLoadingComplete?.(), 200);
      }
    };

    animationId = requestAnimationFrame(updateProgress);

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [isLoading, onLoadingComplete, isHydrated]);

  // Don't render anything until hydrated to prevent hydration mismatch
  if (!isHydrated || !isLoading) return null;

  return (
    <div
      className={`loading-container fixed inset-0 z-50 flex items-center justify-center bg-white dark:bg-black transition-opacity duration-200 ${
        isExiting ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex flex-col items-center space-y-8">
        {/* SynxAI Logo with subtle animation */}
        <div className="w-20 h-20 flex items-center justify-center">
          <svg
            width="60"
            height="60"
            viewBox="0 0 35 33"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={`text-black dark:text-white transition-all duration-500 ${
              progress > 50 ? "scale-105" : "scale-100"
            }`}
            style={{
              // Prevent layout shift during animation
              willChange: "transform",
            }}
          >
            <path
              d="M13.2371 21.0407L24.3186 12.8506C24.8619 12.4491 25.6384 12.6057 25.8973 13.2294C27.2597 16.5185 26.651 20.4712 23.9403 23.1851C21.2297 25.8989 17.4581 26.4941 14.0108 25.1386L10.2449 26.8843C15.6463 30.5806 22.2053 29.6665 26.304 25.5601C29.5551 22.3051 30.562 17.8683 29.6205 13.8673L29.629 13.8758C28.2637 7.99809 29.9647 5.64871 33.449 0.844576C33.5314 0.730667 33.6139 0.616757 33.6964 0.5L29.1113 5.09055V5.07631L13.2343 21.0436"
              fill="currentColor"
            />
          </svg>
        </div>

        {/* Enhanced Progress Bar */}
        <div className="w-64 h-1 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-800">
          <div
            className="h-full rounded-full bg-black dark:bg-white relative overflow-hidden"
            style={{
              width: `${Math.min(progress, 100)}%`,
              transition: "width 0.1s ease-out",
            }}
          >
            {/* Shimmer effect */}
            <div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 dark:via-black/30 to-transparent animate-pulse"
              style={{
                animation:
                  progress > 0 ? "shimmer 1.5s ease-in-out infinite" : "none",
              }}
            />
          </div>
        </div>

        {/* Loading text with fade animation */}
        <div
          className={`text-sm text-gray-600 dark:text-gray-400 transition-opacity duration-300 ${
            progress > 80 ? "opacity-50" : "opacity-100"
          }`}
        ></div>
      </div>

      <style jsx>{`
        .loading-container {
          min-height: 100vh;
          min-height: 100dvh;
          /* Ensure proper mobile viewport handling */
          -webkit-overflow-scrolling: touch;
          overscroll-behavior: none;
        }

        @supports (height: 100dvh) {
          .loading-container {
            min-height: 100dvh;
          }
        }

        /* Prevent zoom on double tap for mobile */
        .loading-container * {
          touch-action: manipulation;
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        /* Optimize for mobile performance */
        @media (max-width: 768px) {
          .loading-container {
            /* Use hardware acceleration */
            transform: translateZ(0);
            backface-visibility: hidden;
          }
        }
      `}</style>
    </div>
  );
}
