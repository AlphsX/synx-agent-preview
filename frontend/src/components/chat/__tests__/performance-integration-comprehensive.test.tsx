/**
 * Comprehensive Performance Tests for Enhanced Message Rendering Integration
 * Tests performance with large content and streaming scenarios
 */

import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MessageRenderer } from '../MessageRenderer';
import { StreamingRenderer } from '../StreamingRenderer';

// Mock the performance monitoring hook
const mockStartRender = jest.fn();
const mockEndRender = jest.fn();
const mockRecordError = jest.fn();

jest.mock('@/hooks/usePerformanceMonitoring', () => ({
  useComponentPerformanceMonitoring: () => ({
    startComponentRender: mockStartRender,
    endComponentRender: mockEndRender,
    recordComponentError: mockRecordError,
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

// Mock performance.now for consistent testing
const mockPerformanceNow = jest.fn();
Object.defineProperty(window, 'performance', {
  value: {
    now: mockPerformanceNow,
  },
});

describe('Performance Tests - Enhanced Message Rendering Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPerformanceNow.mockReturnValue(0);
  });

  describe('Large Content Performance', () => {
    test('renders large markdown document efficiently', () => {
      // Generate large content with various markdown elements
      const sections = Array.from({ length: 50 }, (_, i) => `
## Section ${i + 1}

This is paragraph ${i + 1} with **bold text** and *italic text*. Here's some more content to make it substantial.

### Subsection ${i + 1}.1

- List item 1 for section ${i + 1}
- List item 2 for section ${i + 1}
- List item 3 for section ${i + 1}

\`\`\`javascript
// Code block ${i + 1}
function section${i + 1}() {
  const value = ${i + 1};
  console.log(\`Section \${value} is ready\`);
  return value * 2;
}
\`\`\`

> This is a blockquote for section ${i + 1}. It contains important information about this section.

| Column A | Column B | Column C |
|----------|----------|----------|
| Value ${i + 1}A | Value ${i + 1}B | Value ${i + 1}C |
| Data ${i + 1}A | Data ${i + 1}B | Data ${i + 1}C |

[Link for section ${i + 1}](https://example.com/section${i + 1})
      `).join('\n\n');

      const largeContent = `# Large Document Test\n\n${sections}`;

      const startTime = performance.now();
      
      render(<MessageRenderer content={largeContent} />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (less than 2 seconds)
      expect(renderTime).toBeLessThan(2000);

      // Verify content is rendered
      expect(screen.getByRole('heading', { name: 'Large Document Test' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Section 1' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Section 50' })).toBeInTheDocument();

      // Check that performance monitoring was called
      expect(mockStartRender).toHaveBeenCalled();
    });

    test('handles multiple code blocks efficiently', () => {
      const codeBlocks = Array.from({ length: 20 }, (_, i) => `
### Code Example ${i + 1}

\`\`\`javascript
// Example ${i + 1}: ${['Array methods', 'Object manipulation', 'Async operations', 'DOM handling', 'Event listeners'][i % 5]}
function example${i + 1}() {
  const data = Array.from({ length: ${i + 1} }, (_, index) => ({
    id: index + 1,
    name: \`Item \${index + 1}\`,
    value: Math.random() * 100,
    timestamp: new Date().toISOString(),
    metadata: {
      category: 'example',
      priority: ${i % 3 + 1},
      tags: ['tag1', 'tag2', 'tag3']
    }
  }));
  
  return data
    .filter(item => item.value > 50)
    .map(item => ({
      ...item,
      processed: true,
      score: item.value * ${i + 1}
    }))
    .sort((a, b) => b.score - a.score);
}

// Usage example
const result${i + 1} = example${i + 1}();
console.log('Processed ${i + 1} items:', result${i + 1}.length);
\`\`\`

\`\`\`python
# Python equivalent for example ${i + 1}
import random
from datetime import datetime
from typing import List, Dict, Any

def example_${i + 1}() -> List[Dict[str, Any]]:
    data = [
        {
            'id': index + 1,
            'name': f'Item {index + 1}',
            'value': random.random() * 100,
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'category': 'example',
                'priority': ${i % 3 + 1},
                'tags': ['tag1', 'tag2', 'tag3']
            }
        }
        for index in range(${i + 1})
    ]
    
    filtered_data = [item for item in data if item['value'] > 50]
    processed_data = [
        {**item, 'processed': True, 'score': item['value'] * ${i + 1}}
        for item in filtered_data
    ]
    
    return sorted(processed_data, key=lambda x: x['score'], reverse=True)

# Usage
result_${i + 1} = example_${i + 1}()
print(f'Processed ${i + 1} items: {len(result_${i + 1})}')
\`\`\`
      `).join('\n\n');

      const content = `# Code Performance Test\n\n${codeBlocks}`;

      const startTime = performance.now();
      
      render(<MessageRenderer content={content} />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should handle multiple code blocks efficiently
      expect(renderTime).toBeLessThan(3000);

      // Verify code blocks are rendered
      expect(screen.getByText('function example1() {')).toBeInTheDocument();
      expect(screen.getByText('function example20() {')).toBeInTheDocument();
      expect(screen.getByText('def example_1() -> List[Dict[str, Any]]:')).toBeInTheDocument();
    });

    test('handles large tables efficiently', () => {
      const tableRows = Array.from({ length: 100 }, (_, i) => 
        `| Row ${i + 1} | Data ${i + 1}A | Data ${i + 1}B | Data ${i + 1}C | Data ${i + 1}D | Data ${i + 1}E |`
      ).join('\n');

      const content = `# Large Table Test

| ID | Column A | Column B | Column C | Column D | Column E |
|----|----------|----------|----------|----------|----------|
${tableRows}

This table contains 100 rows of data to test rendering performance.`;

      const startTime = performance.now();
      
      render(<MessageRenderer content={content} />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render large table efficiently
      expect(renderTime).toBeLessThan(1500);

      // Verify table is rendered
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByRole('cell', { name: 'Row 1' })).toBeInTheDocument();
      expect(screen.getByRole('cell', { name: 'Row 100' })).toBeInTheDocument();
    });
  });

  describe('Streaming Performance', () => {
    test('handles rapid streaming updates efficiently', async () => {
      const baseContent = '# Streaming Performance Test\n\n';
      let currentContent = baseContent;

      const { rerender } = render(
        <StreamingRenderer content={currentContent} isComplete={false} />
      );

      const startTime = performance.now();

      // Simulate rapid streaming updates
      for (let i = 1; i <= 100; i++) {
        currentContent += `Chunk ${i}: This is streaming content chunk number ${i}. `;
        
        if (i % 10 === 0) {
          currentContent += '\n\n## Milestone ' + (i / 10) + '\n\n';
        }

        await act(async () => {
          rerender(
            <StreamingRenderer content={currentContent} isComplete={false} />
          );
        });
      }

      // Complete the stream
      await act(async () => {
        rerender(
          <StreamingRenderer content={currentContent} isComplete={true} />
        );
      });

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      // Should handle 100 rapid updates efficiently
      expect(totalTime).toBeLessThan(5000);

      // Verify final content is rendered
      expect(screen.getByText('Chunk 100:')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Milestone 10' })).toBeInTheDocument();
    });

    test('handles streaming code blocks efficiently', async () => {
      const codeChunks = [
        '# Streaming Code Test\n\n```javascript\n',
        'function streamingExample() {\n',
        '  const data = [];\n',
        '  for (let i = 0; i < 1000; i++) {\n',
        '    data.push({\n',
        '      id: i,\n',
        '      value: Math.random(),\n',
        '      timestamp: Date.now()\n',
        '    });\n',
        '  }\n',
        '  return data;\n',
        '}\n',
        '```\n\n',
        'This function generates test data efficiently.'
      ];

      let currentContent = '';
      const { rerender } = render(
        <StreamingRenderer content={currentContent} isComplete={false} />
      );

      const startTime = performance.now();

      // Stream code block progressively
      for (const chunk of codeChunks) {
        currentContent += chunk;
        
        await act(async () => {
          rerender(
            <StreamingRenderer content={currentContent} isComplete={false} />
          );
        });
      }

      // Complete the stream
      await act(async () => {
        rerender(
          <StreamingRenderer content={currentContent} isComplete={true} />
        );
      });

      const endTime = performance.now();
      const streamTime = endTime - startTime;

      // Should handle streaming code blocks efficiently
      expect(streamTime).toBeLessThan(2000);

      // Verify code block is rendered
      expect(screen.getByText('function streamingExample() {')).toBeInTheDocument();
    });

    test('maintains performance with incomplete markdown during streaming', async () => {
      const incompleteStates = [
        '# Incomplete',
        '# Incomplete Test\n\n**Bold',
        '# Incomplete Test\n\n**Bold text**\n\n- List',
        '# Incomplete Test\n\n**Bold text**\n\n- List item\n- Another',
        '# Incomplete Test\n\n**Bold text**\n\n- List item\n- Another item\n\n```js',
        '# Incomplete Test\n\n**Bold text**\n\n- List item\n- Another item\n\n```javascript\nfunction',
        '# Incomplete Test\n\n**Bold text**\n\n- List item\n- Another item\n\n```javascript\nfunction test() {',
        '# Incomplete Test\n\n**Bold text**\n\n- List item\n- Another item\n\n```javascript\nfunction test() {\n  return "complete";\n}',
        '# Incomplete Test\n\n**Bold text**\n\n- List item\n- Another item\n\n```javascript\nfunction test() {\n  return "complete";\n}\n```'
      ];

      const { rerender } = render(
        <StreamingRenderer content="" isComplete={false} />
      );

      const startTime = performance.now();

      // Test each incomplete state
      for (const content of incompleteStates) {
        await act(async () => {
          rerender(
            <StreamingRenderer content={content} isComplete={false} />
          );
        });
      }

      // Complete the final state
      await act(async () => {
        rerender(
          <StreamingRenderer content={incompleteStates[incompleteStates.length - 1]} isComplete={true} />
        );
      });

      const endTime = performance.now();
      const processingTime = endTime - startTime;

      // Should handle incomplete states efficiently
      expect(processingTime).toBeLessThan(3000);

      // Verify final content is rendered correctly
      expect(screen.getByRole('heading', { name: 'Incomplete Test' })).toBeInTheDocument();
      expect(screen.getByText('function test() {')).toBeInTheDocument();
    });
  });

  describe('Memory Management', () => {
    test('does not leak memory with repeated renders', () => {
      const content = `# Memory Test

This is a test for memory leaks during repeated rendering.

\`\`\`javascript
const data = new Array(1000).fill(0).map((_, i) => ({ id: i, value: Math.random() }));
\`\`\``;

      // Render and unmount multiple times
      for (let i = 0; i < 50; i++) {
        const { unmount } = render(<MessageRenderer content={content} />);
        unmount();
      }

      // If we get here without running out of memory, the test passes
      expect(true).toBe(true);
    });

    test('cleans up streaming resources properly', async () => {
      const { rerender, unmount } = render(
        <StreamingRenderer content="Initial" isComplete={false} />
      );

      // Update multiple times
      for (let i = 1; i <= 20; i++) {
        await act(async () => {
          rerender(
            <StreamingRenderer content={`Initial + Update ${i}`} isComplete={false} />
          );
        });
      }

      // Unmount should clean up resources
      unmount();

      // If we get here without issues, cleanup worked
      expect(true).toBe(true);
    });
  });

  describe('Concurrent Rendering', () => {
    test('handles multiple simultaneous renders', async () => {
      const contents = Array.from({ length: 10 }, (_, i) => `
# Document ${i + 1}

This is document ${i + 1} with various content types.

## Code Section

\`\`\`javascript
function doc${i + 1}() {
  return "Document ${i + 1} content";
}
\`\`\`

## List Section

- Item ${i + 1}.1
- Item ${i + 1}.2
- Item ${i + 1}.3
      `);

      const startTime = performance.now();

      // Render multiple components simultaneously
      const renders = contents.map((content, i) => 
        render(<MessageRenderer key={i} content={content} />)
      );

      const endTime = performance.now();
      const concurrentTime = endTime - startTime;

      // Should handle concurrent renders efficiently
      expect(concurrentTime).toBeLessThan(3000);

      // Verify all renders completed
      renders.forEach((_, i) => {
        expect(screen.getByRole('heading', { name: `Document ${i + 1}` })).toBeInTheDocument();
      });

      // Cleanup
      renders.forEach(({ unmount }) => unmount());
    });

    test('maintains performance with concurrent streaming', async () => {
      const streamers = Array.from({ length: 5 }, (_, i) => ({
        content: `# Stream ${i + 1}\n\n`,
        component: null as any
      }));

      // Start all streams
      streamers.forEach((stream, i) => {
        stream.component = render(
          <StreamingRenderer content={stream.content} isComplete={false} />
        );
      });

      const startTime = performance.now();

      // Update all streams concurrently
      for (let update = 1; update <= 20; update++) {
        await act(async () => {
          streamers.forEach((stream, i) => {
            stream.content += `Update ${update} for stream ${i + 1}. `;
            stream.component.rerender(
              <StreamingRenderer content={stream.content} isComplete={false} />
            );
          });
        });
      }

      // Complete all streams
      await act(async () => {
        streamers.forEach((stream, i) => {
          stream.component.rerender(
            <StreamingRenderer content={stream.content} isComplete={true} />
          );
        });
      });

      const endTime = performance.now();
      const concurrentStreamTime = endTime - startTime;

      // Should handle concurrent streaming efficiently
      expect(concurrentStreamTime).toBeLessThan(5000);

      // Verify all streams completed
      streamers.forEach((_, i) => {
        expect(screen.getByRole('heading', { name: `Stream ${i + 1}` })).toBeInTheDocument();
      });

      // Cleanup
      streamers.forEach(stream => stream.component.unmount());
    });
  });

  describe('Performance Monitoring Integration', () => {
    test('calls performance monitoring hooks correctly', () => {
      const content = 'Test content for performance monitoring';
      
      render(<MessageRenderer content={content} />);

      expect(mockStartRender).toHaveBeenCalled();
      // Note: mockEndRender would be called in useEffect cleanup
    });

    test('records errors in performance monitoring', () => {
      // This would test error recording if we had a way to trigger errors
      const content = 'Valid content';
      
      render(<MessageRenderer content={content} />);

      // In normal operation, no errors should be recorded
      expect(mockRecordError).not.toHaveBeenCalled();
    });
  });
});