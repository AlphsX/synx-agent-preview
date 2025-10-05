"use client";

import { Moon, Sun, Monitor } from "lucide-react";

type Props = {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  isUsingSystemPreference?: boolean;
  className?: string;
};

export const AnimatedThemeToggler = ({
  isDarkMode,
  toggleDarkMode,
  isUsingSystemPreference = false,
  className,
}: Props) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();
    toggleDarkMode();
  };

  // Show system icon if using system preference, otherwise show current theme icon
  const showSystemIcon = isUsingSystemPreference;
  const showSunIcon = !showSystemIcon && !isDarkMode;
  const showMoonIcon = !showSystemIcon && isDarkMode;

  return (
    <button
      onClick={handleClick}
      className={`${className} transition-all duration-500 ease-out active:scale-90 relative overflow-hidden transform-gpu`}
      aria-label={
        showSystemIcon
          ? "Using system theme preference"
          : isDarkMode
          ? "Switch to light mode"
          : "Switch to dark mode"
      }
    >
      <div className="relative w-5 h-5">
        {/* System Icon */}
        <div
          className={`absolute inset-0 transition-all duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)] ${
            showSystemIcon
              ? "opacity-100 rotate-0 scale-100"
              : "opacity-0 rotate-[360deg] scale-0"
          }`}
        >
          <Monitor size={20} />
        </div>

        {/* Sun Icon */}
        <div
          className={`absolute inset-0 transition-all duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)] ${
            showSunIcon
              ? "opacity-100 rotate-0 scale-100"
              : "opacity-0 rotate-[360deg] scale-0"
          } theme-toggle-glow-sun`}
        >
          <Sun size={20} />
        </div>

        {/* Moon Icon */}
        <div
          className={`absolute inset-0 transition-all duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)] ${
            showMoonIcon
              ? "opacity-100 rotate-0 scale-100"
              : "opacity-0 rotate-[-360deg] scale-0"
          } theme-toggle-glow-moon`}
        >
          <Moon size={20} />
        </div>
      </div>
    </button>
  );
};
