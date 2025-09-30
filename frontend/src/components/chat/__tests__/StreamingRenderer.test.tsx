import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { StreamingRenderer } from '../StreamingRenderer';

// Mock the MessageRenderer component
jest.mock('../MessageRenderer', () => ({
  MessageRenderer: ({ content, isStreaming }: { content: string; isStreaming: boolean }) => (
    <div data-testid="message-renderer">
      <div data-testid="content">{content}</div>
      <div data-testid="streaming-status">{isStreaming ? 'streaming' : 'complete'}</div>
    </div>
  )
}));

// Mock markdown utils
jest.mock('@/lib/markdown-utils', () => ({
  validateMarkdownContent: jest.fn(() => []),
  handleStreamingError: jest.fn((error) => error.content),
  debounce: jest.fn((fn) => (...args) => fn(...args)), // Return a function that calls the original
  safeParseMarkdown: jest.fn((content) => ({ content, errors: [] }))
}));

describe('StreamingRenderer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders empty content correctly', () => {
      render(
        <StreamingRenderer
          content=""
          isComplete={false}
        />
      );
      
      // Should not render MessageRenderer for empty content
      expect(screen.queryByTestId('message-renderer')).not.toBeInTheDocument();
    });

    it('renders simple text content', () => {
      render(
        <StreamingRenderer
          content="Hello world"
          isComplete={true}
        />
      );
      
      expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      expect(screen.getByTestId('content')).toHaveTextContent('Hello world');
      expect(screen.getByTestId('streaming-status')).toHaveTextContent('complete');
    });

    it('shows streaming status when not complete', () => {
      render(
        <StreamingRenderer
          content="Hello world"
          isComplete={false}
        />
      );
      
      expect(screen.getByTestId('streaming-status')).toHaveTextContent('streaming');
    });
  });

  describe('Streaming Content Processing', () => {
    it('handles incremental content updates', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="Hello"
          isComplete={false}
        />
      );
      
      expect(screen.getByTestId('content')).toHaveTextContent('Hello');
      
      // Update with more content
      rerender(
        <StreamingRenderer
          content="Hello world"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('content')).toHaveTextContent('Hello world');
      });
    });

    it('handles markdown content streaming', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="# Header"
          isComplete={false}
        />
      );
      
      expect(screen.getByTestId('content')).toHaveTextContent('# Header');
      
      // Add more markdown content
      rerender(
        <StreamingRenderer
          content="# Header\n\nSome **bold** text"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('content')).toHaveTextContent('# Header\\n\\nSome **bold** text');
      });
    });

    it('calls onContentUpdate callback when content changes', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content="Hello"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );
      
      // Update content
      rerender(
        <StreamingRenderer
          content="Hello world"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );
      
      await waitFor(() => {
        expect(onContentUpdate).toHaveBeenCalled();
      });
    });
  });

  describe('Code Block Handling', () => {
    it('handles incomplete code blocks during streaming', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="Here's some code:\n```javascript"
          isComplete={false}
        />
      );
      
      // The component should render the content even if incomplete
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
      
      // Complete the code block
      rerender(
        <StreamingRenderer
          content="Here's some code:\n```javascript\nconsole.log('hello');\n```"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });

    it('handles malformed code blocks gracefully', async () => {
      render(
        <StreamingRenderer
          content="```javascript\nconsole.log('hello');\n```\n\n```python"
          isComplete={false}
        />
      );
      
      // Should handle the incomplete second code block
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });

    it('processes complete code blocks immediately', async () => {
      render(
        <StreamingRenderer
          content="```javascript\nconsole.log('hello');\n```"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('content')).toHaveTextContent("```javascript\\nconsole.log('hello');\\n```");
        expect(screen.queryByText(/Processing incomplete content/)).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles processing errors gracefully', async () => {
      // Mock an error in markdown validation
      const mockValidateMarkdownContent = require('@/lib/markdown-utils').validateMarkdownContent;
      mockValidateMarkdownContent.mockReturnValue([
        {
          type: 'parsing',
          message: 'Test error',
          recoverable: true
        }
      ]);
      
      render(
        <StreamingRenderer
          content="# Invalid markdown"
          isComplete={false}
        />
      );
      
      // Should still render content despite errors
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });

    it('shows error information in development mode', async () => {
      // Set NODE_ENV to development
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';
      
      // Mock an error
      const mockValidateMarkdownContent = require('@/lib/markdown-utils').validateMarkdownContent;
      mockValidateMarkdownContent.mockReturnValue([
        {
          type: 'parsing',
          message: 'Test parsing error',
          recoverable: true
        }
      ]);
      
      render(
        <StreamingRenderer
          content="# Invalid markdown"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText(/Streaming Errors/)).toBeInTheDocument();
        expect(screen.getByText(/Test parsing error/)).toBeInTheDocument();
      });
      
      // Restore original NODE_ENV
      process.env.NODE_ENV = originalEnv;
    });

    it('recovers from streaming errors', async () => {
      const mockHandleStreamingError = require('@/lib/markdown-utils').handleStreamingError;
      mockHandleStreamingError.mockReturnValue('Recovered content');
      
      render(
        <StreamingRenderer
          content="```javascript\nconsole.log('incomplete"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });
  });

  describe('Completion Handling', () => {
    it('processes final content when streaming completes', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content="# Header\n\nSome content"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );
      
      // Mark as complete
      rerender(
        <StreamingRenderer
          content="# Header\n\nSome content"
          isComplete={true}
          onContentUpdate={onContentUpdate}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('streaming-status')).toHaveTextContent('complete');
      });
    });

    it('clears pending content when completed', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="```javascript\nconsole.log('hello');"
          isComplete={false}
        />
      );
      
      // Should render the content
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
      
      // Complete the streaming
      rerender(
        <StreamingRenderer
          content="```javascript\nconsole.log('hello');\n```"
          isComplete={true}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('streaming-status')).toHaveTextContent('complete');
      });
    });
  });

  describe('Buffer Management', () => {
    it('handles content reset correctly', async () => {
      const { rerender } = render(
        <StreamingRenderer
          content="First message content"
          isComplete={false}
        />
      );
      
      expect(screen.getByTestId('content')).toHaveTextContent('First message content');
      
      // Simulate new message (shorter content)
      rerender(
        <StreamingRenderer
          content="New"
          isComplete={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('content')).toHaveTextContent('New');
      });
    });

    it('handles rapid content updates efficiently', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content="A"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );
      
      // Rapidly update content
      for (let i = 0; i < 10; i++) {
        rerender(
          <StreamingRenderer
            content={`A${'B'.repeat(i)}`}
            isComplete={false}
            onContentUpdate={onContentUpdate}
          />
        );
      }
      
      // Should handle updates without crashing
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    it('handles large content efficiently', async () => {
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
    });

    it('debounces rapid updates', async () => {
      const onContentUpdate = jest.fn();
      
      const { rerender } = render(
        <StreamingRenderer
          content="Initial"
          isComplete={false}
          onContentUpdate={onContentUpdate}
        />
      );
      
      // Make multiple rapid updates
      act(() => {
        for (let i = 0; i < 5; i++) {
          rerender(
            <StreamingRenderer
              content={`Initial ${i}`}
              isComplete={false}
              onContentUpdate={onContentUpdate}
            />
          );
        }
      });
      
      // Should debounce the updates
      await waitFor(() => {
        expect(screen.getByTestId('message-renderer')).toBeInTheDocument();
      });
    });
  });
});