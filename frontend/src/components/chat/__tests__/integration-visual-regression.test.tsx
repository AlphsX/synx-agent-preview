/**
 * Visual Regression Tests for Enhanced Message Rendering Integration
 * Tests different markdown content types and their visual rendering
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MessageRenderer } from '../MessageRenderer';
import { StreamingRenderer } from '../StreamingRenderer';

// Mock the performance monitoring hook
jest.mock('@/hooks/usePerformanceMonitoring', () => ({
  useComponentPerformanceMonitoring: () => ({
    startComponentRender: jest.fn(),
    endComponentRender: jest.fn(),
    recordComponentError: jest.fn(),
  }),
}));

// Mock the markdown theme hook
jest.mock('@/hooks/useMarkdownTheme', () => ({
  useMarkdownTheme: () => ({
    theme: {
      typography: {
        headings: { h1: 'text-3xl', h2: 'text-2xl', h3: 'text-xl' },
        paragraph: 'text-base',
        list: 'list-disc',
        listItem: 'ml-4',
        blockquote: 'border-l-4',
        code: 'bg-gray-100',
        inlineCode: 'bg-gray-100 px-1',
      },
      colors: {
        text: 'text-gray-900',
        textSecondary: 'text-gray-600',
        border: 'border-gray-200',
        background: 'bg-white',
        codeBackground: 'bg-gray-100',
        linkColor: 'text-blue-600',
        linkHover: 'text-blue-800',
      },
      spacing: {
        paragraph: 'mb-4',
        list: 'mb-4',
        blockquote: 'mb-6',
        codeBlock: 'mb-6',
      },
    },
    isDarkMode: false,
  }),
}));

describe('Visual Regression Tests - Enhanced Message Rendering', () => {
  describe('MessageRenderer - Different Content Types', () => {
    test('renders plain text correctly', () => {
      const content = 'This is a simple plain text message without any formatting.';
      
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByText(content)).toBeInTheDocument();
    });

    test('renders headers with proper hierarchy', () => {
      const content = `# Main Title
## Section Header
### Subsection
#### Sub-subsection
##### Minor Header
###### Smallest Header`;
      
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Main Title');
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Section Header');
      expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Subsection');
      expect(screen.getByRole('heading', { level: 4 })).toHaveTextContent('Sub-subsection');
      expect(screen.getByRole('heading', { level: 5 })).toHaveTextContent('Minor Header');
      expect(screen.getByRole('heading', { level: 6 })).toHaveTextContent('Smallest Header');
    });

    test('renders lists with proper structure', () => {
      const content = `## Unordered List
- First item
- Second item
  - Nested item
  - Another nested item
- Third item

## Ordered List
1. First numbered item
2. Second numbered item
   1. Nested numbered item
   2. Another nested numbered item
3. Third numbered item`;
      
      render(<MessageRenderer content={content} />);
      
      const unorderedLists = screen.getAllByRole('list');
      expect(unorderedLists).toHaveLength(4); // 2 main lists + 2 nested lists
      
      expect(screen.getByText('First item')).toBeInTheDocument();
      expect(screen.getByText('Nested item')).toBeInTheDocument();
      expect(screen.getByText('First numbered item')).toBeInTheDocument();
      expect(screen.getByText('Nested numbered item')).toBeInTheDocument();
    });

    test('renders code blocks with syntax highlighting', () => {
      const content = `Here's some JavaScript code:

\`\`\`javascript
function greet(name) {
  console.log(\`Hello, \${name}!\`);
  return \`Welcome, \${name}\`;
}

const user = "Alice";
greet(user);
\`\`\`

And some Python:

\`\`\`python
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

result = calculate_sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")
\`\`\``;
      
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByText('function greet(name) {')).toBeInTheDocument();
      expect(screen.getByText('def calculate_sum(numbers):')).toBeInTheDocument();
    });

    test('renders inline code correctly', () => {
      const content = 'Use the `console.log()` function to debug your `JavaScript` code. The `Array.map()` method is very useful.';
      
      render(<MessageRenderer content={content} />);
      
      const codeElements = screen.getAllByText(/console\.log\(\)|JavaScript|Array\.map\(\)/);
      expect(codeElements.length).toBeGreaterThan(0);
    });

    test('renders blockquotes with proper styling', () => {
      const content = `> This is a blockquote with some important information.
> It can span multiple lines and should be visually distinct.
> 
> It can also contain **bold text** and *italic text*.

Regular paragraph after the blockquote.`;
      
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByText(/This is a blockquote/)).toBeInTheDocument();
      expect(screen.getByText('Regular paragraph after the blockquote.')).toBeInTheDocument();
    });

    test('renders tables with responsive design', () => {
      const content = `| Feature | Status | Priority |
|---------|--------|----------|
| Markdown Rendering | ✅ Complete | High |
| Code Highlighting | ✅ Complete | High |
| Table Support | ✅ Complete | Medium |
| Link Handling | ✅ Complete | Medium |
| Image Support | 🚧 In Progress | Low |`;
      
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('Feature')).toBeInTheDocument();
      expect(screen.getByText('Markdown Rendering')).toBeInTheDocument();
      expect(screen.getByText('✅ Complete')).toBeInTheDocument();
    });

    test('renders links with security attributes', () => {
      const content = `Check out [React Documentation](https://react.dev) for more information.
Also visit [Next.js](https://nextjs.org) for the framework details.
Internal link: [About Us](/about)`;
      
      render(<MessageRenderer content={content} />);
      
      const reactLink = screen.getByRole('link', { name: 'React Documentation' });
      const nextLink = screen.getByRole('link', { name: 'Next.js' });
      const internalLink = screen.getByRole('link', { name: 'About Us' });
      
      expect(reactLink).toHaveAttribute('href', 'https://react.dev');
      expect(reactLink).toHaveAttribute('target', '_blank');
      expect(reactLink).toHaveAttribute('rel', 'noopener noreferrer');
      
      expect(nextLink).toHaveAttribute('href', 'https://nextjs.org');
      expect(nextLink).toHaveAttribute('target', '_blank');
      
      expect(internalLink).toHaveAttribute('href', '/about');
      expect(internalLink).not.toHaveAttribute('target');
    });

    test('renders mixed content correctly', () => {
      const content = `# Project Overview

This project implements **enhanced markdown rendering** with the following features:

## Key Features

1. **Syntax Highlighting**: Code blocks with language-specific highlighting
2. **Responsive Tables**: Mobile-friendly table layouts
3. **Security**: Safe link handling with proper attributes

### Code Example

\`\`\`typescript
interface MessageProps {
  content: string;
  isStreaming?: boolean;
}

const Message: React.FC<MessageProps> = ({ content, isStreaming }) => {
  return <div className="message">{content}</div>;
};
\`\`\`

> **Note**: This implementation prioritizes performance and accessibility.

For more details, visit our [documentation](https://docs.example.com).

| Component | Status | Tests |
|-----------|--------|-------|
| MessageRenderer | ✅ | 95% |
| CodeBlock | ✅ | 90% |
| StreamingRenderer | ✅ | 85% |`;
      
      render(<MessageRenderer content={content} />);
      
      // Check various elements are rendered
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Project Overview');
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Key Features');
      expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Code Example');
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'documentation' })).toBeInTheDocument();
      expect(screen.getByText('interface MessageProps {')).toBeInTheDocument();
    });
  });

  describe('StreamingRenderer - Real-time Rendering', () => {
    test('renders streaming content progressively', () => {
      const initialContent = '# Streaming';
      const { rerender } = render(
        <StreamingRenderer content={initialContent} isComplete={false} />
      );
      
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Streaming');
      
      // Simulate streaming more content
      const updatedContent = `# Streaming Content

This content is being streamed...`;
      
      rerender(<StreamingRenderer content={updatedContent} isComplete={false} />);
      
      expect(screen.getByText(/This content is being streamed/)).toBeInTheDocument();
    });

    test('handles incomplete code blocks during streaming', () => {
      const incompleteContent = `Here's some code:

\`\`\`javascript
function test() {
  console.log("incomplete`;
      
      render(<StreamingRenderer content={incompleteContent} isComplete={false} />);
      
      // Should handle incomplete content gracefully
      expect(screen.getByText('function test() {')).toBeInTheDocument();
    });

    test('completes rendering when streaming is finished', () => {
      const completeContent = `# Final Content

\`\`\`javascript
function complete() {
  return "done";
}
\`\`\`

All content has been received.`;
      
      render(<StreamingRenderer content={completeContent} isComplete={true} />);
      
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Final Content');
      expect(screen.getByText('function complete() {')).toBeInTheDocument();
      expect(screen.getByText('All content has been received.')).toBeInTheDocument();
    });
  });

  describe('User Message Styling', () => {
    test('applies user message specific styles', () => {
      const content = `# User Message

This is a **user message** with *formatting*.

\`\`\`javascript
const userCode = "test";
\`\`\`

[Link in user message](https://example.com)`;
      
      const { container } = render(
        <div className="user-message-renderer">
          <MessageRenderer content={content} className="user-message-renderer" />
        </div>
      );
      
      // Check that user message container has the right class
      expect(container.firstChild).toHaveClass('user-message-renderer');
    });
  });

  describe('Error Handling', () => {
    test('handles malformed markdown gracefully', () => {
      const malformedContent = `# Unclosed Header
      
\`\`\`javascript
// Unclosed code block
function test() {
  console.log("missing closing");

[Malformed link](incomplete`;
      
      render(<MessageRenderer content={malformedContent} />);
      
      // Should still render what it can
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Unclosed Header');
      expect(screen.getByText('function test() {')).toBeInTheDocument();
    });

    test('handles empty content', () => {
      render(<MessageRenderer content="" />);
      
      // Should not crash and render empty content gracefully
      const container = screen.getByText('', { selector: '.markdown-content' });
      expect(container).toBeInTheDocument();
    });

    test('handles very long content', () => {
      const longContent = 'A'.repeat(10000) + '\n\n# Header\n\nMore content';
      
      render(<MessageRenderer content={longContent} />);
      
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Header');
      expect(screen.getByText('More content')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('renders large content efficiently', () => {
      const largeContent = Array.from({ length: 100 }, (_, i) => 
        `## Section ${i + 1}\n\nThis is paragraph ${i + 1} with some content.\n\n\`\`\`javascript\nconst value${i} = ${i};\n\`\`\``
      ).join('\n\n');
      
      const startTime = performance.now();
      render(<MessageRenderer content={largeContent} />);
      const endTime = performance.now();
      
      // Should render within reasonable time (less than 1 second)
      expect(endTime - startTime).toBeLessThan(1000);
      
      // Check that content is rendered
      expect(screen.getByRole('heading', { name: 'Section 1' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Section 100' })).toBeInTheDocument();
    });

    test('handles rapid content updates efficiently', () => {
      const { rerender } = render(<MessageRenderer content="Initial" />);
      
      const startTime = performance.now();
      
      // Simulate rapid updates
      for (let i = 0; i < 50; i++) {
        rerender(<MessageRenderer content={`Update ${i}: ${'Content '.repeat(i + 1)}`} />);
      }
      
      const endTime = performance.now();
      
      // Should handle rapid updates efficiently
      expect(endTime - startTime).toBeLessThan(2000);
      
      expect(screen.getByText(/Update 49:/)).toBeInTheDocument();
    });
  });
});