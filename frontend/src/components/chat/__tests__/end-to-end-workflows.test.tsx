/**
 * End-to-End Workflow Tests for Enhanced Message Rendering Integration
 * Tests complete user workflows and interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

// Mock clipboard API
const mockWriteText = jest.fn(() => Promise.resolve());
Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText,
  },
});

// Mock window.open for link testing
const mockWindowOpen = jest.fn();
Object.assign(window, {
  open: mockWindowOpen,
});

describe('End-to-End Workflow Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete Chat Message Workflow', () => {
    test('renders a complete AI response with mixed content', async () => {
      const aiResponse = `# AI Assistant Response

Thank you for your question about **React development**. Here's a comprehensive guide:

## Getting Started

To create a new React application, you can use:

\`\`\`bash
npx create-react-app my-app
cd my-app
npm start
\`\`\`

## Key Concepts

1. **Components**: Building blocks of React applications
2. **Props**: Data passed to components
3. **State**: Component's internal data
4. **Hooks**: Functions that let you use state and lifecycle features

### Component Example

\`\`\`jsx
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
}

export default Counter;
\`\`\`

## Best Practices

> **Important**: Always follow React best practices for optimal performance and maintainability.

| Practice | Description | Priority |
|----------|-------------|----------|
| Use Hooks | Modern way to handle state | High |
| Component Composition | Break down complex UIs | High |
| PropTypes | Type checking for props | Medium |
| Testing | Write tests for components | High |

## Resources

For more information, check out:
- [React Documentation](https://react.dev)
- [React Tutorial](https://react.dev/learn)
- [Create React App](https://create-react-app.dev)

Happy coding! 🚀`;

      render(<MessageRenderer content={aiResponse} />);

      // Verify all content types are rendered
      expect(screen.getByRole('heading', { name: 'AI Assistant Response' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Getting Started' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Key Concepts' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Component Example' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Best Practices' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Resources' })).toBeInTheDocument();

      // Verify code blocks
      expect(screen.getByText('npx create-react-app my-app')).toBeInTheDocument();
      expect(screen.getByText('import React, { useState } from \'react\';')).toBeInTheDocument();

      // Verify lists
      expect(screen.getByText('Components')).toBeInTheDocument();
      expect(screen.getByText('Props')).toBeInTheDocument();
      expect(screen.getByText('State')).toBeInTheDocument();
      expect(screen.getByText('Hooks')).toBeInTheDocument();

      // Verify table
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Practice' })).toBeInTheDocument();
      expect(screen.getByRole('cell', { name: 'Use Hooks' })).toBeInTheDocument();

      // Verify blockquote
      expect(screen.getByText(/Important/)).toBeInTheDocument();

      // Verify links
      expect(screen.getByRole('link', { name: 'React Documentation' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'React Tutorial' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Create React App' })).toBeInTheDocument();
    });

    test('handles user message with code and formatting', () => {
      const userMessage = `I'm having trouble with this **React component**:

\`\`\`jsx
function MyComponent() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetchData().then(setData);
  }, []);
  
  return <div>{data ? data.message : 'Loading...'}</div>;
}
\`\`\`

Can you help me understand why it's not working? The \`fetchData\` function returns a Promise.`;

      render(
        <div className="user-message-renderer">
          <MessageRenderer content={userMessage} className="user-message-renderer" />
        </div>
      );

      // Verify user message content
      expect(screen.getByText(/having trouble with this/)).toBeInTheDocument();
      expect(screen.getByText('function MyComponent() {')).toBeInTheDocument();
      expect(screen.getByText('const [data, setData] = useState(null);')).toBeInTheDocument();
      expect(screen.getByText(/Can you help me understand/)).toBeInTheDocument();
    });
  });

  describe('Streaming Response Workflow', () => {
    test('simulates complete streaming response workflow', async () => {
      const streamingSteps = [
        '# Streaming Response',
        '# Streaming Response\n\nI\'ll help you with that question.',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:\n\n1. First point',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:\n\n1. First point\n2. Second point',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:\n\n1. First point\n2. Second point\n\n```javascript',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:\n\n1. First point\n2. Second point\n\n```javascript\nfunction example() {',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:\n\n1. First point\n2. Second point\n\n```javascript\nfunction example() {\n  return "complete";\n}',
        '# Streaming Response\n\nI\'ll help you with that question.\n\n## Analysis\n\nLet me break this down:\n\n1. First point\n2. Second point\n\n```javascript\nfunction example() {\n  return "complete";\n}\n```\n\nThat should help!'
      ];

      const { rerender } = render(
        <StreamingRenderer content={streamingSteps[0]} isComplete={false} />
      );

      // Simulate streaming updates
      for (let i = 1; i < streamingSteps.length; i++) {
        rerender(
          <StreamingRenderer content={streamingSteps[i]} isComplete={false} />
        );

        // Verify content is progressively rendered
        expect(screen.getByRole('heading', { name: 'Streaming Response' })).toBeInTheDocument();
        
        if (i >= 2) {
          expect(screen.getByRole('heading', { name: 'Analysis' })).toBeInTheDocument();
        }
        
        if (i >= 4) {
          expect(screen.getByText('First point')).toBeInTheDocument();
        }
        
        if (i >= 8) {
          expect(screen.getByText('function example() {')).toBeInTheDocument();
        }
      }

      // Complete the stream
      rerender(
        <StreamingRenderer content={streamingSteps[streamingSteps.length - 1]} isComplete={true} />
      );

      // Verify final content
      expect(screen.getByText('That should help!')).toBeInTheDocument();
      expect(screen.getByText('return "complete";')).toBeInTheDocument();
    });

    test('handles streaming with incomplete markdown gracefully', async () => {
      const incompleteSteps = [
        '# Incomplete',
        '# Incomplete **bold',
        '# Incomplete **bold text**',
        '# Incomplete **bold text**\n\n- List',
        '# Incomplete **bold text**\n\n- List item\n- Another',
        '# Incomplete **bold text**\n\n- List item\n- Another item\n\n```js',
        '# Incomplete **bold text**\n\n- List item\n- Another item\n\n```javascript\nfunction test() {',
        '# Incomplete **bold text**\n\n- List item\n- Another item\n\n```javascript\nfunction test() {\n  return "done";\n}\n```'
      ];

      const { rerender } = render(
        <StreamingRenderer content={incompleteSteps[0]} isComplete={false} />
      );

      // Test each incomplete state
      for (const content of incompleteSteps) {
        rerender(
          <StreamingRenderer content={content} isComplete={false} />
        );

        // Should not crash with incomplete content
        expect(screen.getByRole('heading', { name: /Incomplete/ })).toBeInTheDocument();
      }

      // Complete the final state
      rerender(
        <StreamingRenderer content={incompleteSteps[incompleteSteps.length - 1]} isComplete={true} />
      );

      expect(screen.getByText('function test() {')).toBeInTheDocument();
    });
  });

  describe('Interactive Elements Workflow', () => {
    test('complete code copy workflow', async () => {
      const user = userEvent.setup();
      const codeContent = `function calculateSum(numbers) {
  return numbers.reduce((sum, num) => sum + num, 0);
}

const result = calculateSum([1, 2, 3, 4, 5]);
console.log('Sum:', result);`;

      const content = `Here's a utility function:

\`\`\`javascript
${codeContent}
\`\`\`

You can copy this code and use it in your project.`;

      render(<MessageRenderer content={content} />);

      // Find and click the copy button
      const copyButton = screen.getByRole('button', { name: /copy/i });
      expect(copyButton).toBeInTheDocument();

      await user.click(copyButton);

      // Verify clipboard was called with correct content
      expect(mockWriteText).toHaveBeenCalledWith(codeContent);
    });

    test('complete link interaction workflow', async () => {
      const user = userEvent.setup();
      const content = `Check out these resources:

- [React Documentation](https://react.dev) - Official React docs
- [Next.js Guide](https://nextjs.org/docs) - Next.js documentation
- [Internal Guide](/guides/react) - Our internal guide

External links open in new tabs, internal links navigate normally.`;

      render(<MessageRenderer content={content} />);

      // Test external link
      const reactLink = screen.getByRole('link', { name: /React Documentation/ });
      expect(reactLink).toHaveAttribute('target', '_blank');
      expect(reactLink).toHaveAttribute('rel', 'noopener noreferrer');

      // Test internal link
      const internalLink = screen.getByRole('link', { name: /Internal Guide/ });
      expect(internalLink).not.toHaveAttribute('target');
      expect(internalLink).toHaveAttribute('href', '/guides/react');

      // Test keyboard navigation
      await user.tab();
      expect(reactLink).toHaveFocus();

      await user.tab();
      const nextLink = screen.getByRole('link', { name: /Next.js Guide/ });
      expect(nextLink).toHaveFocus();

      await user.tab();
      expect(internalLink).toHaveFocus();
    });
  });

  describe('Theme Integration Workflow', () => {
    test('renders correctly in light theme', () => {
      const content = `# Light Theme Test

This content should look good in **light theme**.

\`\`\`javascript
const theme = 'light';
console.log(\`Current theme: \${theme}\`);
\`\`\`

> This blockquote should be readable in light theme.

[Light theme link](https://example.com)`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Light Theme Test' })).toBeInTheDocument();
      expect(screen.getByText(/light theme/)).toBeInTheDocument();
      expect(screen.getByText('const theme = \'light\';')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Light theme link' })).toBeInTheDocument();
    });

    test('user message styling workflow', () => {
      const userContent = `I need help with this **TypeScript** interface:

\`\`\`typescript
interface User {
  id: number;
  name: string;
  email: string;
  preferences?: {
    theme: 'light' | 'dark';
    notifications: boolean;
  };
}
\`\`\`

How can I make the \`preferences\` field required?`;

      render(
        <div className="user-message-renderer">
          <MessageRenderer content={userContent} className="user-message-renderer" />
        </div>
      );

      // Verify user message content with special styling
      expect(screen.getByText(/need help with this/)).toBeInTheDocument();
      expect(screen.getByText('interface User {')).toBeInTheDocument();
      expect(screen.getByText(/How can I make the/)).toBeInTheDocument();
    });
  });

  describe('Error Recovery Workflow', () => {
    test('recovers from malformed markdown gracefully', () => {
      const malformedContent = `# Error Recovery Test

This content has **unclosed bold text

And an unclosed code block:
\`\`\`javascript
function broken() {
  console.log("missing closing");

[Broken link](incomplete-url

But the rest should still render:

## Working Section

- This list should work
- Even with errors above
- The component should be resilient

\`\`\`python
# This code block should work
def working_function():
    return "success"
\`\`\``;

      // Should not throw an error
      expect(() => {
        render(<MessageRenderer content={malformedContent} />);
      }).not.toThrow();

      // Should still render what it can
      expect(screen.getByRole('heading', { name: 'Error Recovery Test' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Working Section' })).toBeInTheDocument();
      expect(screen.getByText('This list should work')).toBeInTheDocument();
      expect(screen.getByText('def working_function():')).toBeInTheDocument();
    });

    test('handles streaming errors gracefully', async () => {
      const errorSteps = [
        '# Error Test',
        '# Error Test\n\n**Bold',
        '# Error Test\n\n**Bold text**\n\n```js',
        '# Error Test\n\n**Bold text**\n\n```javascript\nfunction test() {',
        '# Error Test\n\n**Bold text**\n\n```javascript\nfunction test() {\n  return "recovered";\n}\n```'
      ];

      const { rerender } = render(
        <StreamingRenderer content={errorSteps[0]} isComplete={false} />
      );

      // Each step should render without errors
      for (const content of errorSteps) {
        expect(() => {
          rerender(
            <StreamingRenderer content={content} isComplete={false} />
          );
        }).not.toThrow();

        expect(screen.getByRole('heading', { name: 'Error Test' })).toBeInTheDocument();
      }

      // Final state should be complete
      rerender(
        <StreamingRenderer content={errorSteps[errorSteps.length - 1]} isComplete={true} />
      );

      expect(screen.getByText('return "recovered";')).toBeInTheDocument();
    });
  });

  describe('Performance Under Load Workflow', () => {
    test('handles rapid content updates efficiently', async () => {
      const baseContent = '# Performance Test\n\n';
      let currentContent = baseContent;

      const { rerender } = render(
        <MessageRenderer content={currentContent} />
      );

      const startTime = performance.now();

      // Simulate rapid updates
      for (let i = 1; i <= 50; i++) {
        currentContent += `Update ${i}: New content added. `;
        
        if (i % 10 === 0) {
          currentContent += `\n\n## Milestone ${i / 10}\n\n`;
        }

        rerender(<MessageRenderer content={currentContent} />);
      }

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      // Should handle rapid updates efficiently
      expect(totalTime).toBeLessThan(3000);

      // Verify final content
      expect(screen.getByText('Update 50:')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Milestone 5' })).toBeInTheDocument();
    });
  });

  describe('Accessibility Workflow', () => {
    test('complete keyboard navigation workflow', async () => {
      const user = userEvent.setup();
      const content = `# Accessibility Test

Navigate through these elements:

[First Link](https://first.com)

\`\`\`javascript
console.log("Code with copy button");
\`\`\`

[Second Link](https://second.com)

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

[Third Link](https://third.com)`;

      render(<MessageRenderer content={content} />);

      // Tab through all focusable elements
      const firstLink = screen.getByRole('link', { name: 'First Link' });
      const copyButton = screen.getByRole('button', { name: /copy/i });
      const secondLink = screen.getByRole('link', { name: 'Second Link' });
      const thirdLink = screen.getByRole('link', { name: 'Third Link' });

      // Navigate with Tab key
      await user.tab();
      expect(firstLink).toHaveFocus();

      await user.tab();
      expect(copyButton).toHaveFocus();

      await user.tab();
      expect(secondLink).toHaveFocus();

      await user.tab();
      expect(thirdLink).toHaveFocus();

      // Test activation with Enter key
      await user.keyboard('{Enter}');
      // In a real browser, this would navigate to the link
    });

    test('screen reader content structure workflow', () => {
      const content = `# Main Document Title

## Introduction Section

This document explains the **key concepts** of our system.

### Important Subsection

Here are the main points:

1. First important point
2. Second important point
3. Third important point

#### Technical Details

\`\`\`javascript
// Code example for screen readers
function accessibleCode() {
  return "This code is properly structured";
}
\`\`\`

## Reference Table

| Feature | Status | Notes |
|---------|--------|-------|
| Accessibility | ✅ Complete | WCAG 2.1 AA compliant |
| Performance | ✅ Complete | Optimized for all devices |
| Testing | 🚧 In Progress | Comprehensive test suite |

## External Resources

For more information, visit:
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [React Accessibility](https://react.dev/learn/accessibility)

> **Note**: This content is structured for optimal screen reader experience.`;

      render(<MessageRenderer content={content} />);

      // Verify proper heading hierarchy
      expect(screen.getByRole('heading', { level: 1, name: 'Main Document Title' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'Introduction Section' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 3, name: 'Important Subsection' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 4, name: 'Technical Details' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'Reference Table' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2, name: 'External Resources' })).toBeInTheDocument();

      // Verify list structure
      const lists = screen.getAllByRole('list');
      expect(lists).toHaveLength(2); // Numbered list + bullet list

      // Verify table structure
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Feature' })).toBeInTheDocument();

      // Verify links have proper attributes
      const wcagLink = screen.getByRole('link', { name: /WCAG Guidelines/ });
      expect(wcagLink).toHaveAttribute('target', '_blank');
      expect(wcagLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });
});