import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CopyButton } from '../CopyButton';

// Mock clipboard API
const mockClipboard = {
  writeText: jest.fn(),
};

Object.assign(navigator, {
  clipboard: mockClipboard,
});

// Mock haptic feedback
const mockVibrate = jest.fn();
Object.assign(navigator, {
  vibrate: mockVibrate,
});

// Mock animation utilities
jest.mock('@/lib/animation-utils', () => ({
  createScaleAnimation: jest.fn(() => ({
    whileHover: { scale: 1.05 },
    whileTap: { scale: 0.95 },
    transition: { duration: 0.15 },
  })),
  useOptimizedAnimation: jest.fn(() => ({
    shouldAnimate: true,
    getAnimationProps: (props: any) => props,
  })),
}));

describe('CopyButton Enhanced Animations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockClipboard.writeText.mockResolvedValue(undefined);
  });

  describe('Animation States', () => {
    it('should apply correct animation classes for different states', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Initial state
      expect(button).toHaveClass('transition-all', 'duration-300', 'ease-out-back');
      
      // Click to trigger copying state
      await user.click(button);
      
      // Should show copying state with animation
      await waitFor(() => {
        expect(button).toHaveClass('scale-95');
      });
      
      // Should transition to success state
      await waitFor(() => {
        expect(button).toHaveClass('animate-copy-success');
      }, { timeout: 1000 });
    });

    it('should show hover animations', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Hover should trigger scale animation
      await user.hover(button);
      
      expect(button).toHaveClass('scale-105', 'shadow-lg');
    });

    it('should show ripple effect on touch', async () => {
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Simulate touch event
      fireEvent.touchStart(button, {
        touches: [{ clientX: 50, clientY: 50 }],
      });
      
      // Should create ripple element
      const ripple = button.querySelector('div[class*="absolute"]');
      expect(ripple).toBeInTheDocument();
    });
  });

  describe('Haptic Feedback', () => {
    it('should trigger haptic feedback on copy', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" enableHapticFeedback={true} />);
      
      const button = screen.getByRole('button');
      await user.click(button);
      
      expect(mockVibrate).toHaveBeenCalledWith(50);
    });

    it('should not trigger haptic feedback when disabled', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" enableHapticFeedback={false} />);
      
      const button = screen.getByRole('button');
      await user.click(button);
      
      expect(mockVibrate).not.toHaveBeenCalled();
    });
  });

  describe('Tooltip Animations', () => {
    it('should show animated tooltip on hover', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" showTooltip={true} />);
      
      const button = screen.getByRole('button');
      
      await user.hover(button);
      
      await waitFor(() => {
        const tooltip = screen.getByText('Copy to clipboard');
        expect(tooltip).toBeInTheDocument();
        expect(tooltip).toHaveClass('animate-fade-in-up');
      });
    });

    it('should update tooltip text based on state', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" showTooltip={true} />);
      
      const button = screen.getByRole('button');
      
      // Initial tooltip
      await user.hover(button);
      expect(screen.getByText('Copy to clipboard')).toBeInTheDocument();
      
      // Click to copy
      await user.click(button);
      
      // Should show success tooltip
      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument();
      });
    });
  });

  describe('Performance Optimizations', () => {
    it('should use GPU acceleration classes', () => {
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('transform-gpu', 'will-change-transform');
    });

    it('should respect reduced motion preferences', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      const { useOptimizedAnimation } = require('@/lib/animation-utils');
      useOptimizedAnimation.mockReturnValue({
        shouldAnimate: false,
        getAnimationProps: () => ({}),
      });

      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Should not have animation classes when reduced motion is preferred
      expect(button).not.toHaveClass('gpu-accelerated');
    });
  });

  describe('Error State Animations', () => {
    it('should animate error state when copy fails', async () => {
      mockClipboard.writeText.mockRejectedValue(new Error('Copy failed'));
      
      const user = userEvent.setup();
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      await user.click(button);
      
      await waitFor(() => {
        expect(button).toHaveClass('shadow-red-200/50');
        expect(screen.getByLabelText(/failed to copy/i)).toBeInTheDocument();
      });
    });
  });

  describe('Mobile Touch Interactions', () => {
    it('should handle touch events with proper feedback', () => {
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Touch start
      fireEvent.touchStart(button, {
        touches: [{ clientX: 100, clientY: 100 }],
      });
      
      // Should apply touch feedback styles
      expect(button.style.transform).toContain('scale');
      
      // Touch end
      fireEvent.touchEnd(button, {
        changedTouches: [{ clientX: 100, clientY: 100 }],
      });
    });

    it('should create ripple effect at touch position', () => {
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      fireEvent.touchStart(button, {
        touches: [{ clientX: 75, clientY: 25 }],
      });
      
      const ripple = button.querySelector('div[class*="absolute"]');
      expect(ripple).toBeInTheDocument();
      
      // Ripple should be positioned at touch point
      expect(ripple).toHaveStyle({
        left: expect.stringContaining('px'),
        top: expect.stringContaining('px'),
      });
    });
  });

  describe('Accessibility with Animations', () => {
    it('should maintain accessibility during animations', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Should have proper ARIA labels during all states
      expect(button).toHaveAttribute('aria-label', 'Copy to clipboard');
      
      await user.click(button);
      
      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Copied to clipboard successfully');
      });
    });

    it('should support keyboard navigation with animations', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Focus should work with animations
      await user.tab();
      expect(button).toHaveFocus();
      
      // Enter key should trigger copy with animations
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith('test content');
      });
    });
  });

  describe('Animation Cleanup', () => {
    it('should clean up animations on unmount', () => {
      const { unmount } = render(<CopyButton text="test content" />);
      
      // Trigger some animations
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Unmount should not cause memory leaks
      expect(() => unmount()).not.toThrow();
    });

    it('should handle rapid state changes gracefully', async () => {
      const user = userEvent.setup();
      render(<CopyButton text="test content" />);
      
      const button = screen.getByRole('button');
      
      // Rapid clicks should not break animations
      await user.click(button);
      await user.click(button);
      await user.click(button);
      
      // Should still function correctly
      expect(mockClipboard.writeText).toHaveBeenCalled();
    });
  });
});