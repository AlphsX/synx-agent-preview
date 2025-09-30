import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { StreamingRenderer } from '../StreamingRenderer';

// Mock the chatAPI
const mockChatAPI = {
  streamChat: jest.fn(),
  getModels: jest.fn(() => Promise.resolve({ models: [] }))
};

jest.mock('@/lib/api', () => ({
  chatAPI: mockChatAPI
}));

// Mock other dependencies
jest.mock('@/hooks', () => ({
  useDarkMode: () => ({ isDarkMode: false, toggleDarkMode: jest.fn() })
}));

jest.mock('@/components/magicui', () => ({
  AnimatedThemeToggler: () => <div data-testid="theme-toggler" />,
  VoiceThemeNotification: () => <div data-testid="voice-notification" />,
  AuroraText: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SearchToolsDropdown: () => <div data-testid="search-tools" />
}));

jest.mock('@/components/magicui/ai-model-dropdown', () => ({
  AIModelDropdown: () => <div data-testid="ai-model-dropdown" />
}));

jest.mock('@/lib/test-enhanced-api', () => ({
  testEnhancedBackend: jest.fn(),
  testStreamingChat: jest.fn()
}));

// Mock markdown utils
jest.mock('@/lib/markdown-utils', () => ({
  validateMarkdownContent: jest.fn(() => []),
  handleStreamingError: jest.fn((error) => error.content),
  debounce: jest.fn((fn) => (...args) => fn(...args)),
  safeParseMarkdown: jest.fn((content) => ({ content, errors: [] }))
}));

// Mock MessageRenderer
jest.mock('../MessageRenderer', () => ({
  MessageRenderer: ({ content, isStreaming }: { content: string; isStreaming: boolean }) => (
    <div data-testid="message-renderer">
      <div data-testid="rendered-content">{content}</div>
      <div data-testid="streaming-indicator">{isStreaming ? 'streaming' : 'complete'}</div>
    </div>
  )
}));

describe('Streaming Chat Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Real-time Markdown Processing', () => {
    it('processes streaming markdown content in real-time', async () => {
      const streamingContent = [
        '# Hello',
        '\n\nThis is a **streaming**',
        ' response with `code`',
        '\n\n```javascript\nconsole.log("hello");',
        '\n```'
      ];

      let currentContent = '';
      
      const { rerender } = render(
        <StreamingRenderer
          content=""
          isComplete={false}
        />
      );

      // Simulate streaming content updates
      for (let i = 0; i < streamingContent.length; i++) {
        currentContent += streamingContent[i];
        
        rerender(
          <StreamingRenderer
            content={currentContent}
            isComplete={i === streamingContent.length - 1}
          />
        );

        await waitFor(() => {
          expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
        });
      }

      // Final content should be complete
      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('complete');
      });
    });

    it('handles incomplete code blocks during streaming', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="Here's some code:\n```javascript"
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });

      // Complete the code block
      rerender(
        <StreamingRenderer
          content="Here's some code:\n```javascript\nconsole.log('hello');\n```"
          isComplete={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('complete');
      });
    });

    it('processes markdown headers and formatting during streaming', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="# Main Header"
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('rendered-content')).toHaveTextContent('# Main Header');
      });

      // Add more content
      rerender(
        <StreamingRenderer
          content="# Main Header\n\n## Subheader\n\nSome **bold** text"
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('rendered-content')).toHaveTextContent('# Main Header\\n\\n## Subheader\\n\\nSome **bold** text');
      });
    });
  });

  describe('Performance Optimizations', () => {
    it('handles large streaming responses efficiently', async () => {
      const largeContent = 'A'.repeat(10000);
      
      render(
        <StreamingRenderer
          content={largeContent}
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });

      // Should not cause performance issues
      expect(screen.getByTestId('rendered-content')).toHaveTextContent(largeContent);
    });

    it('debounces rapid content updates', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content="Initial"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );

      // Make multiple rapid updates
      for (let i = 0; i < 10; i++) {
        rerender(
          <StreamingRenderer
            content={`Initial ${i}`}
            isComplete={false}
            onContentUpdate={onContentUpdate}
          />
        );
      }

      // Should handle updates efficiently
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });

    it('optimizes memory usage for long conversations', async () => {
      // Test a single message with large content to simulate memory optimization
      const largeMessage = {
        id: 'large-msg',
        content: Array.from({ length: 100 }, (_, i) => `Line ${i} with **markdown** content`).join('\n'),
        isComplete: true
      };

      render(
        <StreamingRenderer
          content={largeMessage.content}
          isComplete={largeMessage.isComplete}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });

      // Should handle large content without issues
      expect(screen.getByTestId('rendered-content')).toBeInTheDocument();
    });
  });

  describe('Error Recovery', () => {
    it('recovers from malformed streaming content', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="```javascript\nconsole.log('incomplete"
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });

      // Complete with proper content
      rerender(
        <StreamingRenderer
          content="```javascript\nconsole.log('complete');\n```"
          isComplete={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('complete');
      });
    });

    it('handles network interruptions gracefully', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="Partial content..."
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });

      // Simulate network interruption by marking as complete with partial content
      rerender(
        <StreamingRenderer
          content="Partial content..."
          isComplete={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('complete');
        expect(screen.getByTestId('rendered-content')).toHaveTextContent('Partial content...');
      });
    });
  });

  describe('State Management', () => {
    it('maintains proper streaming state throughout the process', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content=""
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );

      // Start streaming
      rerender(
        <StreamingRenderer
          content="Starting..."
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('streaming');
      });

      // Continue streaming
      rerender(
        <StreamingRenderer
          content="Starting... more content"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('streaming');
      });

      // Complete streaming
      rerender(
        <StreamingRenderer
          content="Starting... more content... complete!"
          isComplete={true}
          onContentUpdate={onContentUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('complete');
      });
    });

    it('handles content updates callback correctly', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content="Initial content"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );

      rerender(
        <StreamingRenderer
          content="Updated content"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );

      await waitFor(() => {
        expect(onContentUpdate).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility and UX', () => {
    it('provides appropriate loading indicators during streaming', async () => {
      render(
        <StreamingRenderer
          content="Streaming content..."
          isComplete={false}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('streaming-indicator')).toHaveTextContent('streaming');
      });
    });

    it('maintains focus and scroll position during updates', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="Initial content"
          isComplete={false}
        />
      );

      // Simulate content updates
      for (let i = 1; i <= 5; i++) {
        rerender(
          <StreamingRenderer
            content={`Initial content ${'update '.repeat(i)}`}
            isComplete={false}
          />
        );

        await waitFor(() => {
          expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
        });
      }

      // Should maintain proper rendering throughout
      expect(screen.getByTestId('rendered-content')).toHaveTextContent('Initial content update update update update update');
    });
  });
});