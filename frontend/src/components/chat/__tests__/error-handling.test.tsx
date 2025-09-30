import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MessageRenderer } from '../MessageRenderer';
import { MarkdownErrorBoundary } from '../MarkdownErrorBoundary';
import { CodeBlock } from '../CodeBlock';

// Mock console methods to avoid noise in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

describe('Error Handling Tests', () => {
  describe('MarkdownErrorBoundary', () => {
    // Component that throws an error
    const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>No error</div>;
    };

    test('should catch and display error with fallback content', () => {
      const fallbackContent = 'This is fallback content';
      const onError = jest.fn();

      render(
        <MarkdownErrorBoundary fallbackContent={fallbackContent} onError={onError}>
          <ThrowError shouldThrow={true} />
        </MarkdownErrorBoundary>
      );

      expect(screen.getByText('Content Rendering Error')).toBeInTheDocument();
      expect(screen.getByText(fallbackContent)).toBeInTheDocument();
      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'rendering',
          recoverable: true
        })
      );
    });

    test('should render children normally when no error occurs', () => {
      render(
        <MarkdownErrorBoundary>
          <ThrowError shouldThrow={false} />
        </MarkdownErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
      expect(screen.queryByText('Content Rendering Error')).not.toBeInTheDocument();
    });

    test('should allow retry after error', () => {
      const { rerender } = render(
        <MarkdownErrorBoundary fallbackContent="Fallback">
          <ThrowError shouldThrow={true} />
        </MarkdownErrorBoundary>
      );

      expect(screen.getByText('Content Rendering Error')).toBeInTheDocument();

      // Click retry button
      fireEvent.click(screen.getByText('Try Again'));

      // Re-render with no error
      rerender(
        <MarkdownErrorBoundary fallbackContent="Fallback">
          <ThrowError shouldThrow={false} />
        </MarkdownErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
    });

    test('should show error details in development mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      render(
        <MarkdownErrorBoundary fallbackContent="Fallback">
          <ThrowError shouldThrow={true} />
        </MarkdownErrorBoundary>
      );

      expect(screen.getByText('Error Details (Development)')).toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
    });
  });

  describe('MessageRenderer Error Handling', () => {
    test('should handle malformed markdown gracefully', () => {
      const malformedContent = `
# Header
\`\`\`javascript
// Unclosed code block
[Unclosed link](
      `;

      render(<MessageRenderer content={malformedContent} />);

      // Should still render something
      expect(screen.getByText('Header')).toBeInTheDocument();
    });

    test('should handle empty content', () => {
      render(<MessageRenderer content="" />);
      
      // Should not crash
      expect(document.querySelector('.message-renderer')).toBeInTheDocument();
    });

    test('should handle null/undefined content', () => {
      render(<MessageRenderer content={null as any} />);
      
      // Should not crash
      expect(document.querySelector('.message-renderer')).toBeInTheDocument();
    });

    test('should handle extremely long content', () => {
      const longContent = 'a'.repeat(100000);
      
      render(<MessageRenderer content={longContent} />);
      
      // Should not crash
      expect(document.querySelector('.message-renderer')).toBeInTheDocument();
    });

    test('should handle content with special characters', () => {
      const specialContent = `
# Header with émojis 🚀
\`\`\`javascript
const special = "Special chars: àáâãäåæçèéêë";
console.log(special);
\`\`\`
      `;

      render(<MessageRenderer content={specialContent} />);
      
      expect(screen.getByText(/Header with émojis/)).toBeInTheDocument();
    });

    test('should handle malicious content safely', () => {
      const maliciousContent = `
<script>alert('xss')</script>
<img src="x" onerror="alert('xss')">
[Click me](javascript:alert('xss'))
      `;

      render(<MessageRenderer content={maliciousContent} />);
      
      // Should not execute scripts or render dangerous HTML
      expect(screen.queryByText('alert')).not.toBeInTheDocument();
      expect(document.querySelector('script')).not.toBeInTheDocument();
    });

    test('should show parsing warnings in development mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      const contentWithWarnings = `
# Header
\`\`\`javascript
// Unclosed code block
      `;

      render(<MessageRenderer content={contentWithWarnings} />);

      // Should show warning in development
      expect(screen.getByText(/Parsing Warnings/)).toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
    });
  });

  describe('CodeBlock Error Handling', () => {
    test('should handle copy failures gracefully', async () => {
      // Mock clipboard API to fail
      const originalClipboard = navigator.clipboard;
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: jest.fn().mockRejectedValue(new Error('Clipboard failed'))
        },
        writable: true
      });

      render(
        <CodeBlock language="javascript">
          console.log('test');
        </CodeBlock>
      );

      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(screen.getByText('Copy failed')).toBeInTheDocument();
      });

      // Restore clipboard
      Object.defineProperty(navigator, 'clipboard', {
        value: originalClipboard,
        writable: true
      });
    });

    test('should handle unsupported languages', () => {
      render(
        <CodeBlock language="unsupported-language">
          some code here
        </CodeBlock>
      );

      // Should still render as plaintext
      expect(screen.getByText('some code here')).toBeInTheDocument();
    });

    test('should handle empty code content', () => {
      render(<CodeBlock language="javascript"></CodeBlock>);
      
      // Should not crash
      expect(document.querySelector('.relative.group')).toBeInTheDocument();
    });

    test('should handle very long code blocks', () => {
      const longCode = 'console.log("test");\n'.repeat(1000);
      
      render(
        <CodeBlock language="javascript">
          {longCode}
        </CodeBlock>
      );
      
      // Should render with line numbers for long content
      expect(document.querySelector('[class*="line-number"]')).toBeInTheDocument();
    });

    test('should fallback to execCommand when clipboard API unavailable', async () => {
      // Mock clipboard API as unavailable
      const originalClipboard = navigator.clipboard;
      Object.defineProperty(navigator, 'clipboard', {
        value: undefined,
        writable: true
      });

      // Mock execCommand
      const mockExecCommand = jest.fn().mockReturnValue(true);
      document.execCommand = mockExecCommand;

      render(
        <CodeBlock language="javascript">
          console.log('test');
        </CodeBlock>
      );

      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockExecCommand).toHaveBeenCalledWith('copy');
      });

      // Restore clipboard
      Object.defineProperty(navigator, 'clipboard', {
        value: originalClipboard,
        writable: true
      });
    });
  });

  describe('Performance Error Handling', () => {
    test('should handle performance monitoring errors gracefully', () => {
      // Mock performance.now to throw
      const originalPerformanceNow = performance.now;
      performance.now = jest.fn().mockImplementation(() => {
        throw new Error('Performance API error');
      });

      // Should not crash when performance monitoring fails
      expect(() => {
        render(<MessageRenderer content="# Test content" />);
      }).not.toThrow();

      // Restore performance.now
      performance.now = originalPerformanceNow;
    });

    test('should handle memory monitoring errors gracefully', () => {
      // Mock performance.memory to be unavailable
      const originalMemory = (performance as any).memory;
      delete (performance as any).memory;

      // Should not crash when memory monitoring is unavailable
      expect(() => {
        render(<MessageRenderer content="# Test content" />);
      }).not.toThrow();

      // Restore memory
      if (originalMemory) {
        (performance as any).memory = originalMemory;
      }
    });
  });

  describe('Streaming Error Handling', () => {
    test('should handle incomplete streaming content', () => {
      const incompleteContent = `
# Streaming Header
This is incomplete content with unclosed
      `;

      render(<MessageRenderer content={incompleteContent} isStreaming={true} />);

      expect(screen.getByText('Streaming Header')).toBeInTheDocument();
      expect(screen.getByText('Generating response...')).toBeInTheDocument();
    });

    test('should handle streaming content with malformed code blocks', () => {
      const malformedStreamingContent = `
# Code Example
\`\`\`javascript
function test() {
  console.log('incomplete
      `;

      render(<MessageRenderer content={malformedStreamingContent} isStreaming={true} />);

      expect(screen.getByText('Code Example')).toBeInTheDocument();
    });

    test('should handle rapid streaming updates', () => {
      const { rerender } = render(
        <MessageRenderer content="# Start" isStreaming={true} />
      );

      // Rapidly update content
      for (let i = 0; i < 10; i++) {
        rerender(
          <MessageRenderer 
            content={`# Start\nUpdate ${i}`} 
            isStreaming={true} 
          />
        );
      }

      expect(screen.getByText('Start')).toBeInTheDocument();
      expect(screen.getByText('Update 9')).toBeInTheDocument();
    });
  });

  describe('Link Security Error Handling', () => {
    test('should handle invalid URLs safely', () => {
      const contentWithInvalidLinks = `
[Invalid link](not-a-url)
[JavaScript link](javascript:alert('xss'))
[Data link](data:text/html,<script>alert('xss')</script>)
[Valid link](https://example.com)
      `;

      render(<MessageRenderer content={contentWithInvalidLinks} />);

      // Should show invalid link placeholder
      expect(screen.getByText('[Invalid Link]')).toBeInTheDocument();
      
      // Should render valid link
      expect(screen.getByText('Valid link')).toBeInTheDocument();
      
      // Should not render dangerous links
      expect(screen.queryByText('JavaScript link')).not.toBeInTheDocument();
    });

    test('should handle malformed link syntax', () => {
      const malformedLinks = `
[Unclosed link](
[No URL]()
[Nested [brackets]](https://example.com)
      `;

      render(<MessageRenderer content={malformedLinks} />);

      // Should handle gracefully without crashing
      expect(document.querySelector('.message-renderer')).toBeInTheDocument();
    });
  });
});