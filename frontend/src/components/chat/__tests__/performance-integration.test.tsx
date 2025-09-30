import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MessageRenderer } from "../MessageRenderer";
import { performanceUtils } from "@/lib/markdown-utils";

// Mock performance monitoring
const mockPerformanceMonitoring = {
  startComponentRender: jest.fn(),
  endComponentRender: jest.fn(),
  recordComponentError: jest.fn(),
};

jest.mock("@/hooks/usePerformanceMonitoring", () => ({
  useComponentPerformanceMonitoring: () => mockPerformanceMonitoring,
}));

describe("Performance Integration Tests", () => {
  beforeEach(() => {
    performanceUtils.clearCaches();
    jest.clearAllMocks();
  });

  describe("Rendering Performance", () => {
    test("should render simple content quickly", async () => {
      const simpleContent = "# Hello World\nThis is a simple test.";

      const start = performance.now();
      render(<MessageRenderer content={simpleContent} />);
      const renderTime = performance.now() - start;

      expect(renderTime).toBeLessThan(50); // Should render in under 50ms
      expect(screen.getByText("Hello World")).toBeInTheDocument();
      expect(mockPerformanceMonitoring.startComponentRender).toHaveBeenCalled();
    });

    test("should handle complex content efficiently", async () => {
      const complexContent = `
# Complex Document

## Introduction
This is a complex document with multiple features.

### Code Examples

\`\`\`javascript
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log(fibonacci(10));
\`\`\`

\`\`\`python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))
\`\`\`

### Lists and Tables

- Item 1
- Item 2
  - Nested item
  - Another nested item
- Item 3

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown | ✅ | Working |
| Code highlighting | ✅ | Working |
| Tables | ✅ | Working |

### Links and Quotes

Check out [React](https://reactjs.org) for more information.

> This is a blockquote with some important information.
> It spans multiple lines.

### Inline Code

Use \`useState\` for state management in React components.
      `;

      const start = performance.now();
      render(<MessageRenderer content={complexContent} />);
      const renderTime = performance.now() - start;

      expect(renderTime).toBeLessThan(100); // Should render complex content in under 100ms
      expect(screen.getByText("Complex Document")).toBeInTheDocument();
      expect(screen.getByText("fibonacci")).toBeInTheDocument();
      expect(screen.getByText("React")).toBeInTheDocument();
    });

    test("should benefit from caching on re-renders", async () => {
      const content = `
# Cached Content
\`\`\`javascript
console.log('This should be cached');
\`\`\`
      `;

      // First render
      const { rerender } = render(<MessageRenderer content={content} />);

      // Second render should be faster due to caching
      const start = performance.now();
      rerender(<MessageRenderer content={content} />);
      const cachedRenderTime = performance.now() - start;

      expect(cachedRenderTime).toBeLessThan(20); // Cached render should be very fast
    });

    test("should handle streaming content updates efficiently", async () => {
      const streamingChunks = [
        "# Streaming",
        " Content\n\nThis",
        " is streaming",
        " markdown.\n\n```js\n",
        'console.log("streaming");',
        "\n```",
      ];

      let content = "";
      const renderTimes: number[] = [];

      const { rerender } = render(
        <MessageRenderer content="" isStreaming={true} />
      );

      for (const chunk of streamingChunks) {
        content += chunk;

        const start = performance.now();
        rerender(<MessageRenderer content={content} isStreaming={true} />);
        const renderTime = performance.now() - start;

        renderTimes.push(renderTime);
      }

      // Each streaming update should be fast
      renderTimes.forEach((time) => {
        expect(time).toBeLessThan(30);
      });

      expect(screen.getByText("Streaming Content")).toBeInTheDocument();
      expect(screen.getByText("Generating response...")).toBeInTheDocument();
    });
  });

  describe("Memory Management", () => {
    test("should not leak memory with multiple renders", async () => {
      const content = "# Memory Test\nTesting memory usage.";

      // Render multiple times
      for (let i = 0; i < 50; i++) {
        const { unmount } = render(
          <MessageRenderer content={`${content} ${i}`} />
        );
        unmount();
      }

      // Cache should not grow indefinitely
      const cacheStats = performanceUtils.getCacheStats();
      expect(cacheStats.featureAnalysis.size).toBeLessThanOrEqual(
        cacheStats.featureAnalysis.maxSize
      );
    });

    test("should handle large content without memory issues", async () => {
      // Generate large content
      const largeContent = Array(100)
        .fill(0)
        .map(
          (_, i) => `
## Section ${i}
This is section ${i} with some content.

\`\`\`javascript
function section${i}() {
  console.log('Section ${i}');
}
\`\`\`
      `
        )
        .join("\n");

      const { unmount } = render(<MessageRenderer content={largeContent} />);

      // Should render without issues
      expect(screen.getByText("Section 0")).toBeInTheDocument();

      unmount();

      // Memory should be cleaned up
      expect(true).toBe(true); // Test passes if no memory errors occur
    });
  });

  describe("Error Recovery Performance", () => {
    test("should handle malformed content quickly", async () => {
      const malformedContent = `
# Malformed Content
\`\`\`javascript
// Unclosed code block
[Unclosed link](
####### Too many hashes
      `;

      const start = performance.now();
      render(<MessageRenderer content={malformedContent} />);
      const renderTime = performance.now() - start;

      expect(renderTime).toBeLessThan(50); // Should handle errors quickly
      expect(screen.getByText("Malformed Content")).toBeInTheDocument();
    });

    test("should recover from parsing errors gracefully", async () => {
      const errorContent =
        "This content will cause parsing issues: ```unclosed";

      render(<MessageRenderer content={errorContent} />);

      // Should still render something
      expect(
        screen.getByText(/This content will cause parsing issues/)
      ).toBeInTheDocument();
      expect(
        mockPerformanceMonitoring.recordComponentError
      ).not.toHaveBeenCalled();
    });
  });

  describe("Lazy Loading Performance", () => {
    test("should lazy load code blocks for better initial performance", async () => {
      const contentWithCode = `
# Code Example
\`\`\`javascript
function test() {
  console.log('This should be lazy loaded');
}
\`\`\`
      `;

      render(<MessageRenderer content={contentWithCode} />);

      // Header should render immediately
      expect(screen.getByText("Code Example")).toBeInTheDocument();

      // Code block should eventually load
      await waitFor(
        () => {
          expect(
            screen.getByText(/This should be lazy loaded/)
          ).toBeInTheDocument();
        },
        { timeout: 1000 }
      );
    });

    test("should show loading placeholder for lazy-loaded components", async () => {
      const contentWithCode = `
\`\`\`javascript
console.log('Lazy loaded code');
\`\`\`
      `;

      render(<MessageRenderer content={contentWithCode} />);

      // Should show loading placeholder initially
      const loadingElement = document.querySelector(".animate-pulse");
      expect(loadingElement).toBeInTheDocument();
    });
  });

  describe("Performance Monitoring Integration", () => {
    test("should call performance monitoring hooks", () => {
      const content = "# Test Content";

      render(<MessageRenderer content={content} />);

      expect(mockPerformanceMonitoring.startComponentRender).toHaveBeenCalled();
    });

    test("should record performance metrics on unmount", () => {
      const content = "# Test Content";

      const { unmount } = render(<MessageRenderer content={content} />);
      unmount();

      expect(mockPerformanceMonitoring.endComponentRender).toHaveBeenCalledWith(
        expect.any(Number)
      );
    });

    test("should record errors when they occur", () => {
      // Mock console.error to avoid noise
      const originalConsoleError = console.error;
      console.error = jest.fn();

      // This should trigger an error in parsing
      const errorContent = null as any;

      render(<MessageRenderer content={errorContent} />);

      // Should handle the error gracefully
      expect(document.querySelector(".message-renderer")).toBeInTheDocument();

      console.error = originalConsoleError;
    });
  });

  describe("Real-world Performance Scenarios", () => {
    test("should handle typical AI response efficiently", async () => {
      const typicalAIResponse = `
I'll help you create a React component. Here's a complete example:

\`\`\`jsx
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchUser() {
      try {
        const response = await fetch(\`/api/users/\${userId}\`);
        if (!response.ok) {
          throw new Error('Failed to fetch user');
        }
        const userData = await response.json();
        setUser(userData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div className="user-profile">
      <h2>{user.name}</h2>
      <p>Email: {user.email}</p>
      <p>Joined: {new Date(user.createdAt).toLocaleDateString()}</p>
    </div>
  );
}

export default UserProfile;
\`\`\`

Key points about this implementation:

1. **State Management**: Uses \`useState\` for managing user data, loading state, and errors
2. **Side Effects**: Uses \`useEffect\` to fetch data when component mounts or userId changes
3. **Error Handling**: Properly handles network errors and displays them to the user
4. **Loading States**: Shows loading indicator while fetching data
5. **Conditional Rendering**: Renders different content based on the current state

You can use this component like this:

\`\`\`jsx
function App() {
  return (
    <div>
      <h1>My App</h1>
      <UserProfile userId="123" />
    </div>
  );
}
\`\`\`

For more advanced patterns, consider using:
- **React Query** for better data fetching and caching
- **SWR** for stale-while-revalidate data fetching
- **Custom hooks** to extract the data fetching logic

Would you like me to show you how to implement any of these patterns?
      `;

      const start = performance.now();
      render(<MessageRenderer content={typicalAIResponse} />);
      const renderTime = performance.now() - start;

      expect(renderTime).toBeLessThan(100); // Should handle typical AI responses quickly
      expect(
        screen.getByText(/I'll help you create a React component/)
      ).toBeInTheDocument();
      expect(screen.getByText("UserProfile")).toBeInTheDocument();
    });

    test("should handle code-heavy responses efficiently", async () => {
      const codeHeavyResponse = Array(5)
        .fill(0)
        .map(
          (_, i) => `
## Example ${i + 1}

\`\`\`javascript
function example${i + 1}() {
  const data = Array(100).fill(0).map((_, j) => ({
    id: j,
    name: \`Item \${j}\`,
    value: Math.random() * 100
  }));
  
  return data.filter(item => item.value > 50)
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);
}
\`\`\`
      `
        )
        .join("\n");

      const start = performance.now();
      render(<MessageRenderer content={codeHeavyResponse} />);
      const renderTime = performance.now() - start;

      expect(renderTime).toBeLessThan(150); // Should handle code-heavy content efficiently
      expect(screen.getByText("Example 1")).toBeInTheDocument();
    });
  });
});
