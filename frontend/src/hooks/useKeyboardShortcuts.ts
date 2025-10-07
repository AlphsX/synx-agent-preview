"use client";

import { useEffect, useCallback } from "react";

interface KeyboardShortcutsConfig {
  onToggleSidebar?: () => void;
  onToggleTheme?: () => void;
  onFocusInput?: () => void;
  onNewChat?: () => void;
  onToggleTools?: () => void;
}

export function useKeyboardShortcuts(config: KeyboardShortcutsConfig) {
  const {
    onToggleSidebar,
    onToggleTheme,
    onFocusInput,
    onNewChat,
    onToggleTools,
  } = config;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Check for modifier keys (Cmd on Mac, Ctrl on Windows/Linux)
      const isModifierPressed = event.metaKey || event.ctrlKey;

      // Handle "/" key for tools toggle (without modifier)
      if (event.key === "/" && !isModifierPressed && onToggleTools) {
        // Check if the active element is an input, textarea, or contenteditable
        const activeElement = document.activeElement;
        const isInputFocused = activeElement && (
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          activeElement.getAttribute('contenteditable') === 'true'
        );
        
        if (isInputFocused) {
          // Check if this is the first character in the input
          const inputElement = activeElement as HTMLInputElement | HTMLTextAreaElement;
          const currentValue = inputElement.value || '';
          const cursorPosition = inputElement.selectionStart || 0;
          
          // If input is empty or cursor is at the beginning and input is empty
          if (currentValue.length === 0 || (cursorPosition === 0 && currentValue.trim().length === 0)) {
            // Don't prevent default - let "/" be typed in input
            // Use setTimeout to trigger tools after the character is typed
            setTimeout(() => {
              onToggleTools();
            }, 0);
            return;
          }
          // Otherwise, let the "/" character be typed normally
        } else {
          // If no input is focused, trigger tools toggle
          event.preventDefault();
          onToggleTools();
          return;
        }
      }

      if (!isModifierPressed) return;

      // Prevent default behavior for our shortcuts
      switch (event.key) {
        case "[":
          // Cmd+[ or Ctrl+[ - Toggle sidebar
          if (onToggleSidebar) {
            event.preventDefault();
            onToggleSidebar();
          }
          break;

        case "d":
          // Cmd+D or Ctrl+D - Toggle dark mode
          if (onToggleTheme) {
            event.preventDefault();
            onToggleTheme();
          }
          break;

        case "k":
          // Cmd+K or Ctrl+K - Focus input (common shortcut)
          if (onFocusInput) {
            event.preventDefault();
            onFocusInput();
          }
          break;

        case "n":
          // Cmd+N or Ctrl+N - New chat
          if (onNewChat) {
            event.preventDefault();
            onNewChat();
          }
          break;
      }
    },
    [onToggleSidebar, onToggleTheme, onFocusInput, onNewChat, onToggleTools]
  );

  useEffect(() => {
    // Add event listener for keydown events
    document.addEventListener("keydown", handleKeyDown);

    // Cleanup function to remove event listener
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  // Return helper function to check if shortcuts are supported
  return {
    isSupported: typeof window !== "undefined",
    shortcuts: {
      toggleSidebar: navigator.userAgent.includes("Mac") ? "Cmd+[" : "Ctrl+[",
      toggleTheme: navigator.userAgent.includes("Mac") ? "Cmd+D" : "Ctrl+D",
      focusInput: navigator.userAgent.includes("Mac") ? "Cmd+K" : "Ctrl+K",
      newChat: navigator.userAgent.includes("Mac") ? "Cmd+N" : "Ctrl+N",
      toggleTools: "/",
    },
  };
}
