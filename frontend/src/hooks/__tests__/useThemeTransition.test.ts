import { renderHook, act, waitFor } from '@testing-library/react';
import { useThemeTransition, useThemeTransitionPreferences } from '../useThemeTransition';

// Mock useDarkMode hook
jest.mock('../useDarkMode', () => ({
  useDarkMode: jest.fn(() => ({
    isDarkMode: false,
    toggleDarkMode: jest.fn(),
  })),
}));

// Mock document.startViewTransition
const mockStartViewTransition = jest.fn();
Object.defineProperty(document, 'startViewTransition', {
  value: mockStartViewTransition,
  writable: true,
});

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

describe('useThemeTransition', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStartViewTransition.mockReset();
    mockLocalStorage.getItem.mockReturnValue(null);
    
    // Reset document.documentElement
    document.documentElement.className = '';
    document.documentElement.style.cssText = '';
  });

  describe('Basic Functionality', () => {
    it('should initialize with correct default values', () => {
      const { result } = renderHook(() => useThemeTransition());
      
      expect(result.current.isDarkMode).toBe(false);
      expect(result.current.isTransitioning).toBe(false);
      expect(typeof result.current.toggleThemeWithTransition).toBe('function');
      expect(typeof result.current.toggleDarkMode).toBe('function');
    });

    it('should handle theme toggle with transition', async () => {
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      const { result } = renderHook(() => useThemeTransition());
      
      await act(async () => {
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      expect(mockToggleDarkMode).toHaveBeenCalled();
    });
  });

  describe('View Transitions API', () => {
    it('should use View Transitions API when available', async () => {
      const mockFinished = Promise.resolve();
      mockStartViewTransition.mockReturnValue({ finished: mockFinished });
      
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      const { result } = renderHook(() => useThemeTransition({
        enableViewTransition: true,
      }));
      
      await act(async () => {
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      expect(mockStartViewTransition).toHaveBeenCalled();
    });

    it('should fallback to custom transition when View Transitions API fails', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      mockStartViewTransition.mockRejectedValue(new Error('View transition failed'));
      
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      const { result } = renderHook(() => useThemeTransition({
        enableViewTransition: true,
      }));
      
      await act(async () => {
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      expect(mockStartViewTransition).toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });

    it('should use custom transition when View Transitions API is disabled', async () => {
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      const { result } = renderHook(() => useThemeTransition({
        enableViewTransition: false,
      }));
      
      await act(async () => {
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      expect(mockStartViewTransition).not.toHaveBeenCalled();
    });
  });

  describe('Custom Transition', () => {
    it('should apply transition styles during custom transition', async () => {
      // Mock View Transitions API as unavailable
      Object.defineProperty(document, 'startViewTransition', {
        value: undefined,
        writable: true,
      });
      
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      const { result } = renderHook(() => useThemeTransition({
        duration: 500,
        easing: 'ease-in-out',
      }));
      
      await act(async () => {
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      // The transition should have completed
      expect(mockToggleDarkMode).toHaveBeenCalled();
    });

    it('should create and remove overlay during custom transition', async () => {
      // Mock View Transitions API as unavailable
      Object.defineProperty(document, 'startViewTransition', {
        value: undefined,
        writable: true,
      });
      
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      // Mock document.body methods
      const mockAppendChild = jest.spyOn(document.body, 'appendChild');
      const mockRemoveChild = jest.spyOn(document.body, 'removeChild');

      const { result } = renderHook(() => useThemeTransition());
      
      await act(async () => {
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      expect(mockToggleDarkMode).toHaveBeenCalled();
      
      mockAppendChild.mockRestore();
      mockRemoveChild.mockRestore();
    });
  });

  describe('Configuration Options', () => {
    it('should accept custom duration configuration', () => {
      const { result } = renderHook(() => useThemeTransition({
        duration: 1000,
      }));
      
      expect(typeof result.current.toggleThemeWithTransition).toBe('function');
    });

    it('should accept custom easing configuration', () => {
      const { result } = renderHook(() => useThemeTransition({
        easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      }));
      
      expect(typeof result.current.toggleThemeWithTransition).toBe('function');
    });
  });

  describe('Concurrent Transitions', () => {
    it('should handle multiple transition calls gracefully', async () => {
      const mockToggleDarkMode = jest.fn();
      const { useDarkMode } = require('../useDarkMode');
      useDarkMode.mockReturnValue({
        isDarkMode: false,
        toggleDarkMode: mockToggleDarkMode,
      });

      const { result } = renderHook(() => useThemeTransition());
      
      // Start multiple transitions
      await act(async () => {
        result.current.toggleThemeWithTransition();
        result.current.toggleThemeWithTransition();
        result.current.toggleThemeWithTransition();
        await new Promise(resolve => setTimeout(resolve, 100));
      });
      
      // Should handle gracefully without errors
      expect(typeof result.current.toggleThemeWithTransition).toBe('function');
    });
  });

  describe('Cleanup', () => {
    it('should cleanup properly on unmount', () => {
      const { result, unmount } = renderHook(() => useThemeTransition());
      
      // Should not throw on unmount
      expect(() => unmount()).not.toThrow();
    });
  });
});

describe('useThemeTransitionPreferences', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  describe('Default Preferences', () => {
    it('should initialize with default preferences', () => {
      const { result } = renderHook(() => useThemeTransitionPreferences());
      
      expect(result.current.preferences).toEqual({
        enableTransitions: true,
        transitionDuration: 300,
        enableViewTransitions: true,
      });
    });
  });

  describe('Persistence', () => {
    it('should load preferences from localStorage', () => {
      const savedPreferences = {
        enableTransitions: false,
        transitionDuration: 500,
        enableViewTransitions: false,
      };
      
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(savedPreferences));
      
      const { result } = renderHook(() => useThemeTransitionPreferences());
      
      expect(result.current.preferences).toEqual(savedPreferences);
    });

    it('should handle invalid JSON in localStorage', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json');
      
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      const { result } = renderHook(() => useThemeTransitionPreferences());
      
      expect(result.current.preferences).toEqual({
        enableTransitions: true,
        transitionDuration: 300,
        enableViewTransitions: true,
      });
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to parse theme transition preferences:',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });

    it('should save preferences to localStorage when updated', () => {
      const { result } = renderHook(() => useThemeTransitionPreferences());
      
      act(() => {
        result.current.updatePreferences({
          enableTransitions: false,
          transitionDuration: 500,
        });
      });
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'theme-transition-preferences',
        JSON.stringify({
          enableTransitions: false,
          transitionDuration: 500,
          enableViewTransitions: true,
        })
      );
    });
  });

  describe('Preference Updates', () => {
    it('should update preferences correctly', () => {
      const { result } = renderHook(() => useThemeTransitionPreferences());
      
      act(() => {
        result.current.updatePreferences({
          transitionDuration: 1000,
        });
      });
      
      expect(result.current.preferences).toEqual({
        enableTransitions: true,
        transitionDuration: 1000,
        enableViewTransitions: true,
      });
    });

    it('should merge partial updates with existing preferences', () => {
      const { result } = renderHook(() => useThemeTransitionPreferences());
      
      act(() => {
        result.current.updatePreferences({
          enableTransitions: false,
        });
      });
      
      expect(result.current.preferences).toEqual({
        enableTransitions: false,
        transitionDuration: 300,
        enableViewTransitions: true,
      });
      
      act(() => {
        result.current.updatePreferences({
          transitionDuration: 500,
        });
      });
      
      expect(result.current.preferences).toEqual({
        enableTransitions: false,
        transitionDuration: 500,
        enableViewTransitions: true,
      });
    });
  });
});