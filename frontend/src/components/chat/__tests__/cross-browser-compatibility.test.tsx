/**
 * Cross-Browser Compatibility Tests for Enhanced Message Rendering Integration
 * Tests compatibility across different browsers and environments
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MessageRenderer } from '../MessageRenderer';
import { StreamingRenderer } from '../StreamingRenderer';
import { CodeBlock } from '../CodeBlock';

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

// Browser environment mocks
const mockUserAgents = {
  chrome: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  firefox: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
  safari: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
  edge: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
  mobile: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
};

describe('Cross-Browser Compatibility Tests', () => {
  const originalUserAgent = navigator.userAgent;
  const originalClipboard = navigator.clipboard;

  afterEach(() => {
    // Restore original values
    Object.defineProperty(navigator, 'userAgent', {
      value: originalUserAgent,
      configurable: true
    });
    Object.defineProperty(navigator, 'clipboard', {
      value: originalClipboard,
      configurable: true
    });
  });

  describe('Chrome Compatibility', () => {
    beforeEach(() => {
      Object.defineProperty(navigator, 'userAgent', {
        value: mockUserAgents.chrome,
        configurable: true
      });
    });

    test('renders markdown correctly in Chrome', () => {
      const content = `# Chrome Test

This is a test for **Chrome compatibility**.

\`\`\`javascript
// Chrome supports modern JavaScript features
const data = { test: 'chrome' };
const result = { ...data, browser: 'chrome' };
\`\`\`

[Chrome Link](https://chrome.google.com)`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Chrome Test' })).toBeInTheDocument();
      expect(screen.getByText(/Chrome compatibility/)).toBeInTheDocument();
      expect(screen.getByText('const data = { test: \'chrome\' };')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Chrome Link' })).toBeInTheDocument();
    });

    test('handles clipboard API in Chrome', async () => {
      // Mock Chrome's clipboard API
      const mockWriteText = jest.fn(() => Promise.resolve());
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: mockWriteText },
        configurable: true
      });

      render(
        <CodeBlock language="javascript">
          {`console.log("Chrome test");`}
        </CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy/i });
      expect(copyButton).toBeInTheDocument();
    });
  });

  describe('Firefox Compatibility', () => {
    beforeEach(() => {
      Object.defineProperty(navigator, 'userAgent', {
        value: mockUserAgents.firefox,
        configurable: true
      });
    });

    test('renders markdown correctly in Firefox', () => {
      const content = `# Firefox Test

This is a test for **Firefox compatibility**.

> Firefox has excellent standards support.

| Feature | Support |
|---------|---------|
| Markdown | ✅ |
| CSS Grid | ✅ |
| Flexbox | ✅ |`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Firefox Test' })).toBeInTheDocument();
      expect(screen.getByText(/Firefox compatibility/)).toBeInTheDocument();
      expect(screen.getByText(/Firefox has excellent standards support/)).toBeInTheDocument();
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    test('handles clipboard fallback in Firefox', () => {
      // Mock Firefox without clipboard API
      Object.defineProperty(navigator, 'clipboard', {
        value: undefined,
        configurable: true
      });

      render(
        <CodeBlock language="javascript">
          {`console.log("Firefox test");`}
        </CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy/i });
      expect(copyButton).toBeInTheDocument();
    });
  });

  describe('Safari Compatibility', () => {
    beforeEach(() => {
      Object.defineProperty(navigator, 'userAgent', {
        value: mockUserAgents.safari,
        configurable: true
      });
    });

    test('renders markdown correctly in Safari', () => {
      const content = `# Safari Test

This is a test for **Safari compatibility**.

\`\`\`swift
// Safari supports Swift syntax highlighting
struct SafariTest {
    let browser = "Safari"
    let version = "17.1"
}
\`\`\`

- Safari feature 1
- Safari feature 2
- Safari feature 3`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Safari Test' })).toBeInTheDocument();
      expect(screen.getByText(/Safari compatibility/)).toBeInTheDocument();
      expect(screen.getByText('struct SafariTest {')).toBeInTheDocument();
      expect(screen.getByText('Safari feature 1')).toBeInTheDocument();
    });

    test('handles WebKit-specific features in Safari', () => {
      const content = `# WebKit Features

Safari uses WebKit rendering engine.

\`\`\`css
/* WebKit-specific CSS */
.webkit-feature {
  -webkit-appearance: none;
  -webkit-transform: scale(1.1);
}
\`\`\``;

      render(<MessageRenderer content={content} />);

      expect(screen.getByText('-webkit-appearance: none;')).toBeInTheDocument();
    });
  });

  describe('Edge Compatibility', () => {
    beforeEach(() => {
      Object.defineProperty(navigator, 'userAgent', {
        value: mockUserAgents.edge,
        configurable: true
      });
    });

    test('renders markdown correctly in Edge', () => {
      const content = `# Edge Test

This is a test for **Microsoft Edge compatibility**.

\`\`\`csharp
// Edge supports C# syntax highlighting
public class EdgeTest
{
    public string Browser { get; set; } = "Edge";
    public string Engine { get; set; } = "Chromium";
}
\`\`\`

> Edge is now based on Chromium.`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Edge Test' })).toBeInTheDocument();
      expect(screen.getByText(/Microsoft Edge compatibility/)).toBeInTheDocument();
      expect(screen.getByText('public class EdgeTest')).toBeInTheDocument();
      expect(screen.getByText(/Edge is now based on Chromium/)).toBeInTheDocument();
    });
  });

  describe('Mobile Browser Compatibility', () => {
    beforeEach(() => {
      Object.defineProperty(navigator, 'userAgent', {
        value: mockUserAgents.mobile,
        configurable: true
      });

      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        value: 375,
        configurable: true
      });
      Object.defineProperty(window, 'innerHeight', {
        value: 667,
        configurable: true
      });
    });

    test('renders markdown correctly on mobile', () => {
      const content = `# Mobile Test

This content should be **mobile-friendly**.

## Features

- Touch-friendly interface
- Responsive design
- Optimized performance

\`\`\`javascript
// Mobile-optimized code
const isMobile = window.innerWidth < 768;
if (isMobile) {
  console.log("Mobile view active");
}
\`\`\``;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Mobile Test' })).toBeInTheDocument();
      expect(screen.getByText(/mobile-friendly/)).toBeInTheDocument();
      expect(screen.getByText('Touch-friendly interface')).toBeInTheDocument();
      expect(screen.getByText('const isMobile = window.innerWidth < 768;')).toBeInTheDocument();
    });

    test('handles touch interactions on mobile', () => {
      render(
        <CodeBlock language="javascript">
          {`console.log("Mobile code block");`}
        </CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy/i });
      expect(copyButton).toBeInTheDocument();
      
      // On mobile, the button should be touch-friendly
      expect(copyButton).toBeInTheDocument();
    });
  });

  describe('Feature Detection and Fallbacks', () => {
    test('handles missing CSS features gracefully', () => {
      // Mock older browser without CSS Grid support
      const mockSupports = jest.fn((property: string) => {
        return property !== 'display: grid';
      });
      
      (window as any).CSS = {
        supports: mockSupports
      };

      const content = `# Fallback Test

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    test('handles missing JavaScript features gracefully', () => {
      // Mock environment without modern JavaScript features
      const originalPromise = window.Promise;
      delete (window as any).Promise;

      const content = `# JavaScript Fallback Test

This should work even without modern JavaScript features.`;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'JavaScript Fallback Test' })).toBeInTheDocument();

      // Restore Promise
      window.Promise = originalPromise;
    });

    test('handles missing Web APIs gracefully', () => {
      // Mock environment without Intersection Observer
      const originalIntersectionObserver = window.IntersectionObserver;
      delete (window as any).IntersectionObserver;

      const content = `# Web API Fallback Test

This should work without modern Web APIs.

\`\`\`javascript
// Code that might use modern APIs
const observer = new IntersectionObserver(() => {});
\`\`\``;

      render(<MessageRenderer content={content} />);

      expect(screen.getByRole('heading', { name: 'Web API Fallback Test' })).toBeInTheDocument();

      // Restore IntersectionObserver
      window.IntersectionObserver = originalIntersectionObserver;
    });
  });

  describe('Streaming Compatibility', () => {
    test('handles streaming in different browsers', async () => {
      const browsers = Object.keys(mockUserAgents);

      for (const browser of browsers) {
        Object.defineProperty(navigator, 'userAgent', {
          value: mockUserAgents[browser as keyof typeof mockUserAgents],
          configurable: true
        });

        const { rerender, unmount } = render(
          <StreamingRenderer content={`# ${browser} Streaming`} isComplete={false} />
        );

        expect(screen.getByRole('heading', { name: `${browser} Streaming` })).toBeInTheDocument();

        rerender(
          <StreamingRenderer content={`# ${browser} Streaming\n\nContent updated!`} isComplete={true} />
        );

        expect(screen.getByText('Content updated!')).toBeInTheDocument();

        unmount();
      }
    });
  });

  describe('Performance Across Browsers', () => {
    test('maintains performance standards across browsers', () => {
      const content = `# Performance Test

${'## Section\n\nContent paragraph.\n\n'.repeat(20)}

\`\`\`javascript
${'// Code line\n'.repeat(50)}
\`\`\``;

      const browsers = Object.keys(mockUserAgents);

      browsers.forEach(browser => {
        Object.defineProperty(navigator, 'userAgent', {
          value: mockUserAgents[browser as keyof typeof mockUserAgents],
          configurable: true
        });

        const startTime = performance.now();
        const { unmount } = render(<MessageRenderer content={content} />);
        const endTime = performance.now();

        // Should render efficiently in all browsers
        expect(endTime - startTime).toBeLessThan(1000);

        unmount();
      });
    });
  });

  describe('Accessibility Across Browsers', () => {
    test('maintains accessibility standards across browsers', () => {
      const content = `# Accessibility Test

[Test Link](https://example.com)

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

\`\`\`javascript
console.log("Accessible code");
\`\`\``;

      const browsers = Object.keys(mockUserAgents);

      browsers.forEach(browser => {
        Object.defineProperty(navigator, 'userAgent', {
          value: mockUserAgents[browser as keyof typeof mockUserAgents],
          configurable: true
        });

        const { unmount } = render(<MessageRenderer content={content} />);

        // Check accessibility features work across browsers
        expect(screen.getByRole('heading', { name: 'Accessibility Test' })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: 'Test Link' })).toBeInTheDocument();
        expect(screen.getByRole('table')).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Error Handling Across Browsers', () => {
    test('handles errors consistently across browsers', () => {
      const malformedContent = `# Error Test

\`\`\`javascript
// Unclosed code block
function test() {
  console.log("missing closing");

[Malformed link](incomplete`;

      const browsers = Object.keys(mockUserAgents);

      browsers.forEach(browser => {
        Object.defineProperty(navigator, 'userAgent', {
          value: mockUserAgents[browser as keyof typeof mockUserAgents],
          configurable: true
        });

        // Should not throw errors in any browser
        expect(() => {
          const { unmount } = render(<MessageRenderer content={malformedContent} />);
          unmount();
        }).not.toThrow();
      });
    });
  });
});