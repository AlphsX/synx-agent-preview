"use client";

import { Moon, Sun } from "lucide-react";

type Props = {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  className?: string;
};

export const AnimatedThemeToggler = ({ isDarkMode, toggleDarkMode, className }: Props) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();
    toggleDarkMode();
  };

  return (
    <button 
      onClick={handleClick} 
      className={`${className} transition-all duration-500 ease-out active:scale-90 relative overflow-hidden transform-gpu`}
      aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
    >
      <div className="relative w-5 h-5">
        <div className={`absolute inset-0 transition-all duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)] ${isDarkMode ? 'opacity-0 rotate-[360deg] scale-0' : 'opacity-100 rotate-0 scale-100'} theme-toggle-glow-sun`}>
          <Sun size={20} />
        </div>
        <div className={`absolute inset-0 transition-all duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)] ${isDarkMode ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 rotate-[-360deg] scale-0'} theme-toggle-glow-moon`}>
          <Moon size={20} />
        </div>
      </div>
    </button>
  );
};