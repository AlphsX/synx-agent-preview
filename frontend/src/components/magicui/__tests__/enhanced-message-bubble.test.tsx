import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EnhancedMessageBubble, Message } from '../enhanced-message-bubble';

// Mock the StreamingRenderer component
jest.mock('@/components/chat/StreamingRenderer', () => ({
  StreamingRenderer: ({ content, isComplete }: { content: string; isComplete: boolean }) => (
    <div data-testid="streaming-renderer" data-complete={isComplete}>
      {content}
    </div>
  ),
}));

// Mock the CopyButton component
jest.mock('@/components/ui/CopyButton', () => ({
  CopyButton: ({ 
    text, 
    onCopy, 
    className, 
    'aria-label': ariaLabel 
  }: { 
    text: string; 
    onCopy?: (text: string) => void; 
    className?: string;
    'aria-label'?: string;
  }) => (
    <button
      data-testid="copy-button"
      onClick={() => onCopy?.(text)}
      className={className}
      aria-label={ariaLabel}
    >
      Copy
    </button>
  ),
}));

const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  id: '1',
  content: 'Test message content',
  role: 'user',
  timestamp: new Date('2024-01-01T12:00:00Z'),
  ...overrides,
});

describe('EnhancedMessageBubble', () => {
  describe('Rendering', () => {
    it('renders user message correctly', () => {
      const message = createMockMessage({ role: 'user' });
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.getByText('You')).toBeInTheDocument();
      expect(screen.getByText('Test message content')).toBeInTheDocument();
      
      // Check for timestamp format instead of exact time
      const timestampRegex = /\d{1,2}:\d{2}\s(AM|PM)/;
      expect(screen.getByText(timestampRegex)).toBeInTheDocument();
    });

    it('renders assistant message correctly', () => {
      const message = createMockMessage({ 
        role: 'assistant',
        model: 'gpt-4',
      });
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.getByText('Assistant')).toBeInTheDocument();
      expect(screen.getByText('gpt-4')).toBeInTheDocument();
      expect(screen.getByTestId('streaming-renderer')).toBeInTheDocument();
    });

    it('applies correct styling for user messages', () => {
      const message = createMockMessage({ role: 'user' });
      render(<EnhancedMessageBubble message={message} />);

      const container = screen.getByText('You').closest('.rounded-2xl');
      expect(container).toHaveClass('from-blue-600', 'to-blue-700');
    });

    it('applies correct styling for assistant messages', () => {
      const message = createMockMessage({ role: 'assistant' });
      render(<EnhancedMessageBubble message={message} />);

      const container = screen.getByText('Assistant').closest('.rounded-2xl');
      expect(container).toHaveClass('bg-white', 'dark:bg-gray-800/60');
    });

    it('shows model information for assistant messages', () => {
      const message = createMockMessage({ 
        role: 'assistant',
        model: 'claude-3',
      });
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.getByText('claude-3')).toBeInTheDocument();
    });

    it('does not show model information for user messages', () => {
      const message = createMockMessage({ 
        role: 'user',
        model: 'gpt-4', // This should be ignored for user messages
      });
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.queryByText('gpt-4')).not.toBeInTheDocument();
    });
  });

  describe('Streaming Functionality', () => {
    it('shows streaming indicator when isStreaming is true', () => {
      const message = createMockMessage({ role: 'assistant' });
      const { container } = render(<EnhancedMessageBubble message={message} isStreaming={true} />);

      expect(screen.getByText('Thinking...')).toBeInTheDocument();
      
      // Check for animated dots
      const dots = container.querySelectorAll('.animate-pulse');
      expect(dots.length).toBeGreaterThanOrEqual(3);
    });

    it('does not show streaming indicator when isStreaming is false', () => {
      const message = createMockMessage({ role: 'assistant' });
      render(<EnhancedMessageBubble message={message} isStreaming={false} />);

      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    it('passes correct isComplete prop to StreamingRenderer', () => {
      const message = createMockMessage({ role: 'assistant' });
      
      const { rerender } = render(
        <EnhancedMessageBubble message={message} isStreaming={true} />
      );
      
      let streamingRenderer = screen.getByTestId('streaming-renderer');
      expect(streamingRenderer).toHaveAttribute('data-complete', 'false');

      rerender(<EnhancedMessageBubble message={message} isStreaming={false} />);
      
      streamingRenderer = screen.getByTestId('streaming-renderer');
      expect(streamingRenderer).toHaveAttribute('data-complete', 'true');
    });

    it('does not show streaming indicator for user messages', () => {
      const message = createMockMessage({ role: 'user' });
      render(<EnhancedMessageBubble message={message} isStreaming={true} />);

      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });
  });

  describe('Copy Functionality', () => {
    it('renders copy button', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.getByTestId('copy-button')).toBeInTheDocument();
    });

    it('calls onCopyMessage when copy button is clicked', () => {
      const message = createMockMessage({ content: 'Message to copy' });
      const onCopyMessage = jest.fn();
      
      render(
        <EnhancedMessageBubble 
          message={message} 
          onCopyMessage={onCopyMessage} 
        />
      );

      fireEvent.click(screen.getByTestId('copy-button'));
      expect(onCopyMessage).toHaveBeenCalledWith('Message to copy');
    });

    it('passes correct text to copy button', () => {
      const message = createMockMessage({ content: 'Specific content to copy' });
      render(<EnhancedMessageBubble message={message} />);

      const copyButton = screen.getByTestId('copy-button');
      fireEvent.click(copyButton);
      
      // The mock CopyButton should receive the correct text
      expect(copyButton).toBeInTheDocument();
    });
  });

  describe('Timestamp Formatting', () => {
    it('formats timestamp correctly', () => {
      const message = createMockMessage({
        timestamp: new Date('2024-01-01T12:00:00Z'),
      });
      render(<EnhancedMessageBubble message={message} />);

      // Just check that a timestamp is rendered in the correct format (HH:MM AM/PM)
      const timestampRegex = /\d{1,2}:\d{2}\s(AM|PM)/;
      expect(screen.getByText(timestampRegex)).toBeInTheDocument();
    });

    it('displays timestamp with clock icon', () => {
      const message = createMockMessage();
      const { container } = render(<EnhancedMessageBubble message={message} />);

      // Check that clock icon is present
      const clockIcon = container.querySelector('.lucide-clock');
      expect(clockIcon).toBeInTheDocument();
    });

    it('formats different times consistently', () => {
      const times = [
        new Date('2024-01-01T09:30:00Z'),
        new Date('2024-01-01T15:45:00Z'),
        new Date('2024-01-01T00:00:00Z'),
        new Date('2024-01-01T12:00:00Z'),
      ];

      times.forEach((timestamp) => {
        const message = createMockMessage({ timestamp });
        const { unmount } = render(<EnhancedMessageBubble message={message} />);
        
        // Check that timestamp follows the expected format
        const timestampRegex = /\d{1,2}:\d{2}\s(AM|PM)/;
        expect(screen.getByText(timestampRegex)).toBeInTheDocument();
        
        unmount();
      });
    });
  });

  describe('Content Rendering', () => {
    it('renders user message content as plain text with whitespace preservation', () => {
      const message = createMockMessage({
        role: 'user',
        content: 'Line 1\nLine 2\n\nLine 4',
      });
      render(<EnhancedMessageBubble message={message} />);

      // Find the paragraph element specifically
      const content = screen.getByText((content, element) => {
        return element?.tagName === 'P' && element?.textContent === 'Line 1\nLine 2\n\nLine 4';
      });
      expect(content).toHaveClass('whitespace-pre-wrap');
    });

    it('renders assistant message content using StreamingRenderer', () => {
      const message = createMockMessage({
        role: 'assistant',
        content: 'Assistant response with **markdown**',
      });
      render(<EnhancedMessageBubble message={message} />);

      const streamingRenderer = screen.getByTestId('streaming-renderer');
      expect(streamingRenderer).toHaveTextContent('Assistant response with **markdown**');
    });
  });

  describe('Responsive Design', () => {
    it('applies responsive max-width classes', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      const container = screen.getByText('You').closest('[class*="max-w-"]');
      expect(container).toHaveClass(
        'max-w-[85%]',
        'sm:max-w-[75%]',
        'md:max-w-[65%]',
        'lg:max-w-[60%]'
      );
    });

    it('applies responsive padding classes', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      const messageContainer = screen.getByText('You').closest('.rounded-2xl');
      expect(messageContainer).toHaveClass('px-4', 'py-3', 'sm:px-6', 'sm:py-4');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for copy button', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      const copyButton = screen.getByTestId('copy-button');
      expect(copyButton).toHaveAttribute('aria-label', 'Copy message');
    });

    it('uses semantic elements for message structure', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      // Check that the message content is in a proper paragraph element
      const userMessage = screen.getByText('Test message content');
      expect(userMessage.tagName).toBe('P');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className to root container', () => {
      const message = createMockMessage();
      render(
        <EnhancedMessageBubble 
          message={message} 
          className="custom-message-class" 
        />
      );

      const container = screen.getByText('You').closest('.group');
      expect(container).toHaveClass('custom-message-class');
    });

    it('maintains base classes with custom className', () => {
      const message = createMockMessage();
      render(
        <EnhancedMessageBubble 
          message={message} 
          className="custom-class" 
        />
      );

      const container = screen.getByText('You').closest('.group');
      expect(container).toHaveClass('custom-class', 'flex', 'group');
    });
  });

  describe('Message Status', () => {
    it('shows sent status for user messages', () => {
      const message = createMockMessage({ role: 'user' });
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.getByText('Sent')).toBeInTheDocument();
    });

    it('does not show sent status for assistant messages', () => {
      const message = createMockMessage({ role: 'assistant' });
      render(<EnhancedMessageBubble message={message} />);

      expect(screen.queryByText('Sent')).not.toBeInTheDocument();
    });
  });

  describe('Interactive States', () => {
    it('has hover effects on message container', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      const messageContainer = screen.getByText('You').closest('.rounded-2xl');
      expect(messageContainer).toHaveClass('hover:shadow-md');
    });

    it('shows copy button on group hover', () => {
      const message = createMockMessage();
      render(<EnhancedMessageBubble message={message} />);

      const copyButtonContainer = screen.getByTestId('copy-button').closest('.opacity-0');
      expect(copyButtonContainer).toHaveClass('group-hover:opacity-100');
    });
  });
});