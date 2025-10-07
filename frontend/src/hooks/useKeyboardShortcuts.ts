'use client';

import { useEffect, useCallback } from 'react';

interface KeyboardShortcutsConfig {
  onToggleSidebar?: () => void;
  onToggleTheme?: () => void;
  onFocusInput?: () => void;
  onNewChat?: () => void;
}

export function useKeyboardShortcuts(config: KeyboardShortcutsConfig) {
  const {
    onToggleSidebar,
    onToggleTheme,
    onFocusInput,
    onNewChat
  } = config;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Check for modifier keys (Cmd on Mac, Ctrl on Windows/Linux)
    const isModifierPressed = event.metaKey || event.ctrlKey;
    
    if (!isModifierPressed) return;

    // Prevent default behavior for our shortcuts
    switch (event.key) {
      case '[':
        // Cmd+[ or Ctrl+[ - Toggle sidebar
        if (onToggleSidebar) {
          event.preventDefault();
          onToggleSidebar();
        }
        break;
        
      case 'd':
        // Cmd+D or Ctrl+D - Toggle dark mode
        if (onToggleTheme) {
          event.preventDefault();
          onToggleTheme();
        }
        break;
        
      case 'k':
        // Cmd+K or Ctrl+K - Focus input (common shortcut)
        if (onFocusInput) {
          event.preventDefault();
          onFocusInput();
        }
        break;
        
      case 'n':
        // Cmd+N or Ctrl+N - New chat
        if (onNewChat) {
          event.preventDefault();
          onNewChat();
        }
        break;
    }
  }, [onToggleSidebar, onToggleTheme, onFocusInput, onNewChat]);

  useEffect(() => {
    // Add event listener for keydown events
    document.addEventListener('keydown', handleKeyDown);
    
    // Cleanup function to remove event listener
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Return helper function to check if shortcuts are supported
  return {
    isSupported: typeof window !== 'undefined',
    shortcuts: {
      toggleSidebar: navigator.platform.includes('Mac') ? 'Cmd+[' : 'Ctrl+[',
      toggleTheme: navigator.platform.includes('Mac') ? 'Cmd+D' : 'Ctrl+D',
      focusInput: navigator.platform.includes('Mac') ? 'Cmd+K' : 'Ctrl+K',
      newChat: navigator.platform.includes('Mac') ? 'Cmd+N' : 'Ctrl+N',
    }
  };
}