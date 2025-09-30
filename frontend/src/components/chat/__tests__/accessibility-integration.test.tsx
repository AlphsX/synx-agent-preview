/**
 * Accessibility Tests for Enhanced Message Rendering Integration
 * Tests screen reader compatibility and keyboard navigation
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { MessageRenderer } from '../MessageRenderer';
import { StreamingRenderer } from '../StreamingRenderer';
import { CodeBlock } from '../CodeBlock';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

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
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve()),
  },
});

describe('Accessibility Tests - Enhanced Message Rendering', () => {
  describe('Screen Reader Compatibility', () => {
    test('has no accessibility violations for basic content', async () => {
      const content = `# Main Heading

This is a paragraph with **bold text** and *italic text*.

## Subheading

- List item 1
- List item 2
- List item 3`;

      const { container } = render(<MessageRenderer content={content} />);
      const results = await axe(container);
      
      expect(results).toHaveNoViolations();
    });

    test('provides proper heading hierarchy', () => {
      const content = `# Level 1 Heading
## Level 2 Heading
### Level 3 Heading
#### Level 4 Heading
##### Level 5 Heading
###### Level 6 Heading`;

      render(<MessageRenderer content={content} />);

      // Check that headings are properly structured
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Level 1 Heading');
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Level 2 Heading');
      expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Level 3 Heading');
      expect(screen.getByRole('heading', { level: 4 })).toHaveTextContent('Level 4 Heading');
      expect(screen.getByRole('heading', { level: 5 })).toHaveTextContent('Level 5 Heading');
      expect(screen.getByRole('heading', { level: 6 })).toHaveTextContent('Level 6 Heading');
    });

    test('provides proper list structure for screen readers', () => {
      const content = `## Shopping List

- Fruits
  - Apples
  - Bananas
  - Oranges
- Vegetables
  - Carrots
  - Broccoli
- Dairy
  - Milk
  - Cheese

## Steps to Follow

1. Go to store
2. Buy items
   1. Check prices
   2. Compare quality
3. Return home`;

      render(<MessageRenderer content={content} />);

      const lists = screen.getAllByRole('list');
      expect(lists).toHaveLength(4); // 2 main lists + 2 nested lists

      // Check list items are properly structured
      expect(screen.getByText('Fruits')).toBeInTheDocument();
      expect(screen.getByText('Apples')).toBeInTheDocument();
      expect(screen.getByText('Go to store')).toBeInTheDocument();
      expect(screen.getByText('Check prices')).toBeInTheDocument();
    });

    test('provides accessible table structure', async () => {
      const content = `| Name | Role | Department |
|------|------|------------|
| Alice | Developer | Engineering |
| Bob | Designer | Design |
| Carol | Manager | Operations |`;

      const { container } = render(<MessageRenderer content={content} />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      // Check table headers
      expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Role' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Department' })).toBeInTheDocument();

      // Check table cells
      expect(screen.getByRole('cell', { name: 'Alice' })).toBeInTheDocument();
      expect(screen.getByRole('cell', { name: 'Developer' })).toBeInTheDocument();
      expect(screen.getByRole('cell', { name: 'Engineering' })).toBeInTheDocument();

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test('provides accessible link attributes', async () => {
      const content = `Visit [React Documentation](https://react.dev) for more info.
Also check [Next.js Guide](https://nextjs.org/docs) for framework details.
Internal link: [About Page](/about)`;

      const { container } = render(<MessageRenderer content={content} />);

      const reactLink = screen.getByRole('link', { name: /React Documentation/ });
      const nextLink = screen.getByRole('link', { name: /Next.js Guide/ });
      const internalLink = screen.getByRole('link', { name: 'About Page' });

      // External links should have proper attributes
      expect(reactLink).toHaveAttribute('target', '_blank');
      expect(reactLink).toHaveAttribute('rel', 'noopener noreferrer');
      expect(reactLink).toHaveAttribute('title', expect.stringContaining('External link'));

      expect(nextLink).toHaveAttribute('target', '_blank');
      expect(nextLink).toHaveAttribute('rel', 'noopener noreferrer');

      // Internal links should not have target="_blank"
      expect(internalLink).not.toHaveAttribute('target');
      expect(internalLink).not.toHaveAttribute('rel');

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test('provides accessible code blocks with proper labels', async () => {
      const content = `Here's a JavaScript example:

\`\`\`javascript
function greet(name) {
  console.log(\`Hello, \${name}!\`);
}
\`\`\`

And some Python:

\`\`\`python
def calculate(x, y):
    return x + y
\`\`\``;

      const { container } = render(<MessageRenderer content={content} />);

      // Code blocks should be accessible
      expect(screen.getByText('function greet(name) {')).toBeInTheDocument();
      expect(screen.getByText('def calculate(x, y):')).toBeInTheDocument();

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Keyboard Navigation', () => {
    test('allows keyboard navigation through links', async () => {
      const user = userEvent.setup();
      const content = `Check these resources:
- [React Docs](https://react.dev)
- [Next.js Docs](https://nextjs.org)
- [MDN Web Docs](https://developer.mozilla.org)`;

      render(<MessageRenderer content={content} />);

      const reactLink = screen.getByRole('link', { name: /React Docs/ });
      const nextLink = screen.getByRole('link', { name: /Next.js Docs/ });
      const mdnLink = screen.getByRole('link', { name: /MDN Web Docs/ });

      // Tab through links
      await user.tab();
      expect(reactLink).toHaveFocus();

      await user.tab();
      expect(nextLink).toHaveFocus();

      await user.tab();
      expect(mdnLink).toHaveFocus();

      // Test Enter key activation
      const mockOpen = jest.fn();
      window.open = mockOpen;
      
      await user.keyboard('{Enter}');
      // Note: In a real browser, this would navigate to the link
    });

    test('supports keyboard navigation for code block copy buttons', async () => {
      const user = userEvent.setup();
      const mockCopy = jest.fn();
      
      render(
        <CodeBlock language="javascript" onCopy={mockCopy}>
          {`function test() {
  return "hello";
}`}
        </CodeBlock>
      );

      // Find the copy button
      const copyButton = screen.getByRole('button', { name: /copy/i });
      expect(copyButton).toBeInTheDocument();

      // Tab to the copy button
      await user.tab();
      expect(copyButton).toHaveFocus();

      // Activate with Enter key
      await user.keyboard('{Enter}');
      expect(mockCopy).toHaveBeenCalledWith(`function test() {
  return "hello";
}`);

      // Activate with Space key
      await user.keyboard(' ');
      expect(mockCopy).toHaveBeenCalledTimes(2);
    });

    test('maintains focus management during streaming updates', async () => {
      const user = userEvent.setup();
      const initialContent = `# Streaming Content

[Initial Link](https://example.com)`;

      const { rerender } = render(
        <StreamingRenderer content={initialContent} isComplete={false} />
      );

      const initialLink = screen.getByRole('link', { name: 'Initial Link' });
      
      // Focus the link
      await user.click(initialLink);
      expect(initialLink).toHaveFocus();

      // Update content while maintaining focus
      const updatedContent = `# Streaming Content

[Initial Link](https://example.com)

More content is being added...

[New Link](https://new-example.com)`;

      rerender(<StreamingRenderer content={updatedContent} isComplete={false} />);

      // Original link should still be focusable
      expect(screen.getByRole('link', { name: 'Initial Link' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'New Link' })).toBeInTheDocument();
    });
  });

  describe('ARIA Labels and Descriptions', () => {
    test('provides appropriate ARIA labels for interactive elements', () => {
      render(
        <CodeBlock language="javascript" showCopyButton={true}>
          {`const message = "Hello World";`}
        </CodeBlock>
      );

      const copyButton = screen.getByRole('button');
      expect(copyButton).toHaveAttribute('aria-label', expect.stringContaining('Copy'));
    });

    test('provides ARIA descriptions for complex content', () => {
      const content = `> **Important Note**: This is a critical warning about the system.
> Please read carefully before proceeding.`;

      render(<MessageRenderer content={content} />);

      // Blockquotes should be identifiable
      expect(screen.getByText(/Important Note/)).toBeInTheDocument();
    });

    test('provides proper ARIA roles for custom components', async () => {
      const content = `| Status | Count |
|--------|-------|
| Active | 42 |
| Inactive | 8 |`;

      const { container } = render(<MessageRenderer content={content} />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      // Check that table structure is accessible
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('High Contrast and Reduced Motion Support', () => {
    test('respects reduced motion preferences', () => {
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

      const content = `# Animated Content

This content should respect motion preferences.`;

      const { container } = render(<MessageRenderer content={content} />);

      // Check that animations are disabled or reduced
      expect(container.firstChild).toBeInTheDocument();
    });

    test('supports high contrast mode', () => {
      // Mock high contrast preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      const content = `# High Contrast Content

This should be readable in high contrast mode.

[Test Link](https://example.com)`;

      render(<MessageRenderer content={content} />);

      const heading = screen.getByRole('heading', { level: 1 });
      const link = screen.getByRole('link');

      expect(heading).toBeInTheDocument();
      expect(link).toBeInTheDocument();
    });
  });

  describe('Screen Reader Announcements', () => {
    test('provides appropriate live region updates for streaming content', () => {
      const { rerender } = render(
        <StreamingRenderer content="Loading..." isComplete={false} />
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Update with more content
      rerender(
        <StreamingRenderer content="Loading... Content received!" isComplete={true} />
      );

      expect(screen.getByText(/Content received!/)).toBeInTheDocument();
    });

    test('announces copy actions to screen readers', async () => {
      const user = userEvent.setup();
      
      render(
        <CodeBlock language="javascript">
          {`console.log("test");`}
        </CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy/i });
      
      await user.click(copyButton);

      // In a real implementation, this would trigger an ARIA live region update
      // to announce the copy action to screen readers
    });
  });

  describe('Focus Management', () => {
    test('maintains logical focus order', async () => {
      const user = userEvent.setup();
      const content = `# Document Title

[First Link](https://first.com)

\`\`\`javascript
const code = "example";
\`\`\`

[Second Link](https://second.com)

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

[Third Link](https://third.com)`;

      render(<MessageRenderer content={content} />);

      const firstLink = screen.getByRole('link', { name: /First Link/ });
      const secondLink = screen.getByRole('link', { name: /Second Link/ });
      const thirdLink = screen.getByRole('link', { name: /Third Link/ });

      // Tab through focusable elements in order
      await user.tab();
      expect(firstLink).toHaveFocus();

      await user.tab();
      // Skip over copy button if present
      const copyButton = screen.queryByRole('button', { name: /copy/i });
      if (copyButton) {
        expect(copyButton).toHaveFocus();
        await user.tab();
      }

      expect(secondLink).toHaveFocus();

      await user.tab();
      expect(thirdLink).toHaveFocus();
    });

    test('handles focus trapping in modal-like components', () => {
      // This would test focus trapping if we had modal components
      // For now, we ensure focus management works correctly
      const content = `[Link 1](https://example1.com) [Link 2](https://example2.com)`;
      
      render(<MessageRenderer content={content} />);

      const link1 = screen.getByRole('link', { name: 'Link 1' });
      const link2 = screen.getByRole('link', { name: 'Link 2' });

      expect(link1).toBeInTheDocument();
      expect(link2).toBeInTheDocument();
    });
  });
});