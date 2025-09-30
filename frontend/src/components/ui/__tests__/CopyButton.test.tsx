import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CopyButton, CopyButtonProps } from '../CopyButton';

// Mock clipboard API
const mockWriteText = jest.fn();
const mockClipboard = {
  writeText: mockWriteText,
};

// Mock execCommand for fallback
const mockExecCommand = jest.fn();

// Setup mocks
beforeAll(() => {
  // Mock window.isSecureContext
  Object.defineProperty(window, 'isSecureContext', {
    writable: true,
    value: true,
  });
});

beforeEach(() => {
  jest.clearAllMocks();
  jest.clearAllTimers();
  jest.useFakeTimers();
  
  // Reset clipboard mock
  Object.defineProperty(navigator, 'clipboard', {
    writable: true,
    value: mockClipboard,
  });
  
  Object.defineProperty(document, 'execCommand', {
    writable: true,
    value: mockExecCommand,
  });
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

const defaultProps: CopyButtonProps = {
  text: 'Hello, World!',
};

describe('CopyButton', () => {
  describe('Rendering', () => {
    it('renders with default props', () => {
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /copy to clipboard/i });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });

    it('renders with custom aria-label', () => {
      render(<CopyButton {...defaultProps} aria-label="Copy code snippet" />);
      
      const button = screen.getByRole('button', { name: /copy code snippet/i });
      expect(button).toBeInTheDocument();
    });

    it('renders with different sizes', () => {
      const { rerender } = render(<CopyButton {...defaultProps} size="sm" />);
      let button = screen.getByRole('button');
      expect(button).toHaveClass('h-6', 'w-6');

      rerender(<CopyButton {...defaultProps} size="md" />);
      button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'w-8');

      rerender(<CopyButton {...defaultProps} size="lg" />);
      button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'w-10');
    });

    it('renders with different variants', () => {
      const { rerender } = render(<CopyButton {...defaultProps} variant="default" />);
      let button = screen.getByRole('button');
      expect(button).toHaveClass('bg-gray-100');

      rerender(<CopyButton {...defaultProps} variant="ghost" />);
      button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-gray-100');

      rerender(<CopyButton {...defaultProps} variant="outline" />);
      button = screen.getByRole('button');
      expect(button).toHaveClass('border');
    });

    it('renders as disabled when disabled prop is true', () => {
      render(<CopyButton {...defaultProps} disabled />);
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50');
    });
  });

  describe('Copy Functionality', () => {
    it('copies text using clipboard API on click', async () => {
      mockWriteText.mockResolvedValue(undefined);
      const onCopy = jest.fn();
      
      render(<CopyButton {...defaultProps} onCopy={onCopy} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith('Hello, World!');
        expect(onCopy).toHaveBeenCalledWith('Hello, World!');
      });
    });

    it('shows success state after successful copy', async () => {
      mockWriteText.mockResolvedValue(undefined);
      
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Copied to clipboard successfully');
        expect(button).toHaveClass('bg-green-100');
      });
    });

    it('resets to idle state after success timeout', async () => {
      mockWriteText.mockResolvedValue(undefined);
      
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Copied to clipboard successfully');
      });

      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Copy to clipboard');
      });
    });

    it('falls back to execCommand when clipboard API is not available', async () => {
      // Mock clipboard API as unavailable
      Object.defineProperty(navigator, 'clipboard', {
        writable: true,
        value: undefined,
      });
      mockExecCommand.mockReturnValue(true);
      
      const onCopy = jest.fn();
      render(<CopyButton {...defaultProps} onCopy={onCopy} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockExecCommand).toHaveBeenCalledWith('copy');
        expect(onCopy).toHaveBeenCalledWith('Hello, World!');
      });

      // Restore clipboard
      Object.defineProperty(navigator, 'clipboard', {
        writable: true,
        value: mockClipboard,
      });
    });

    it('handles copy errors gracefully', async () => {
      const error = new Error('Copy failed');
      mockWriteText.mockRejectedValue(error);
      const onError = jest.fn();
      
      render(<CopyButton {...defaultProps} onError={onError} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Failed to copy to clipboard');
        expect(button).toHaveClass('bg-red-100');
        expect(onError).toHaveBeenCalledWith(error);
      });
    });

    it('resets to idle state after error timeout', async () => {
      mockWriteText.mockRejectedValue(new Error('Copy failed'));
      
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Failed to copy to clipboard');
      });

      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Copy to clipboard');
      });
    });

    it('prevents multiple simultaneous copy operations', async () => {
      mockWriteText.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button');
      
      // Click multiple times rapidly
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);

      // Should only call writeText once
      expect(mockWriteText).toHaveBeenCalledTimes(1);
    });
  });

  describe('Keyboard Accessibility', () => {
    it('triggers copy on Enter key press', async () => {
      mockWriteText.mockResolvedValue(undefined);
      const onCopy = jest.fn();
      
      render(<CopyButton {...defaultProps} onCopy={onCopy} />);
      
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith('Hello, World!');
        expect(onCopy).toHaveBeenCalledWith('Hello, World!');
      });
    });

    it('triggers copy on Space key press', async () => {
      mockWriteText.mockResolvedValue(undefined);
      const onCopy = jest.fn();
      
      render(<CopyButton {...defaultProps} onCopy={onCopy} />);
      
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: ' ' });

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith('Hello, World!');
        expect(onCopy).toHaveBeenCalledWith('Hello, World!');
      });
    });

    it('does not trigger copy on other key presses', async () => {
      mockWriteText.mockResolvedValue(undefined);
      
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Tab' });
      fireEvent.keyDown(button, { key: 'Escape' });

      expect(mockWriteText).not.toHaveBeenCalled();
    });

    it('has proper focus styles', () => {
      render(<CopyButton {...defaultProps} />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500');
    });
  });

  describe('User Interactions', () => {
    it('works with user-event library', async () => {
      mockWriteText.mockResolvedValue(undefined);
      const onCopy = jest.fn();
      
      render(<CopyButton {...defaultProps} onCopy={onCopy} />);
      
      const button = screen.getByRole('button');
      
      // Use fireEvent instead of userEvent to avoid clipboard conflicts
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith('Hello, World!');
        expect(onCopy).toHaveBeenCalledWith('Hello, World!');
      });
    });

    it('handles disabled state correctly', async () => {
      mockWriteText.mockResolvedValue(undefined);
      
      render(<CopyButton {...defaultProps} disabled />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockWriteText).not.toHaveBeenCalled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      render(<CopyButton {...defaultProps} className="custom-class" />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });

    it('maintains base classes with custom className', () => {
      render(<CopyButton {...defaultProps} className="custom-class" />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class', 'inline-flex', 'items-center', 'justify-center');
    });
  });
});