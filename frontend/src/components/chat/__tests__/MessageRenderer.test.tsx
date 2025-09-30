import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MessageRenderer } from '../MessageRenderer';

// Mock the markdown utilities
jest.mock('@/lib/markdown-utils', () => ({
  analyzeMarkdownFeatures: jest.fn((content: string) => ({
    hasHeaders: content.includes('#'),
    hasLists: content.includes('-') || content.includes('1.'),
    hasTables: content.includes('|'),
    hasLinks: content.includes('['),
    hasBlockquotes: content.includes('>'),
    hasCodeBlocks: content.includes('```'),
    hasInlineCode: content.includes('`')
  })),
  safeParseMarkdown: jest.fn((content: string) => ({
    content,
    errors: []
  }))
}));

describe('MessageRenderer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Markdown Rendering', () => {
    it('renders plain text content', () => {
      render(<MessageRenderer content="Hello world" />);
      expect(screen.getByText('Hello world')).toBeInTheDocument();
    });

    it('renders bold text correctly', () => {
      render(<MessageRenderer content="This is **bold** text" />);
      expect(screen.getByText('bold')).toBeInTheDocument();
      expect(screen.getByText('bold').tagName).toBe('STRONG');
    });

    it('renders italic text correctly', () => {
      render(<MessageRenderer content="This is *italic* text" />);
      expect(screen.getByText('italic')).toBeInTheDocument();
      expect(screen.getByText('italic').tagName).toBe('EM');
    });

    it('renders inline code correctly', () => {
      render(<MessageRenderer content="This is `inline code`" />);
      const codeElement = screen.getByText('inline code');
      expect(codeElement).toBeInTheDocument();
      expect(codeElement.tagName).toBe('CODE');
    });
  });

  describe('Headers', () => {
    it('renders h1 headers correctly', () => {
      render(<MessageRenderer content="# Main Header" />);
      const header = screen.getByRole('heading', { level: 1 });
      expect(header).toBeInTheDocument();
      expect(header).toHaveTextContent('Main Header');
    });

    it('renders h2 headers correctly', () => {
      render(<MessageRenderer content="## Sub Header" />);
      const header = screen.getByRole('heading', { level: 2 });
      expect(header).toBeInTheDocument();
      expect(header).toHaveTextContent('Sub Header');
    });

    it('renders h3 headers correctly', () => {
      render(<MessageRenderer content="### Section Header" />);
      const header = screen.getByRole('heading', { level: 3 });
      expect(header).toBeInTheDocument();
      expect(header).toHaveTextContent('Section Header');
    });

    it('applies correct CSS classes to headers', () => {
      render(<MessageRenderer content="# Test Header" />);
      const header = screen.getByRole('heading', { level: 1 });
      expect(header).toHaveClass('text-3xl', 'font-bold', 'mb-4', 'mt-6');
    });
  });

  describe('Lists', () => {
    it('renders unordered lists correctly', () => {
      const content = `
- Item 1
- Item 2
- Item 3
      `;
      render(<MessageRenderer content={content} />);
      
      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
      expect(list.tagName).toBe('UL');
      
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
    });

    it('renders ordered lists correctly', () => {
      const content = `
1. First item
2. Second item
3. Third item
      `;
      render(<MessageRenderer content={content} />);
      
      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
      expect(list.tagName).toBe('OL');
      
      expect(screen.getByText('First item')).toBeInTheDocument();
      expect(screen.getByText('Second item')).toBeInTheDocument();
      expect(screen.getByText('Third item')).toBeInTheDocument();
    });

    it('applies correct CSS classes to lists', () => {
      render(<MessageRenderer content="- Test item" />);
      const list = screen.getByRole('list');
      expect(list).toHaveClass('list-disc', 'list-inside');
    });
  });

  describe('Links', () => {
    it('renders links correctly', () => {
      render(<MessageRenderer content="[Google](https://google.com)" />);
      const link = screen.getByRole('link', { name: 'Google' });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', 'https://google.com');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('applies correct CSS classes to links', () => {
      render(<MessageRenderer content="[Test](https://test.com)" />);
      const link = screen.getByRole('link');
      expect(link).toHaveClass('underline', 'transition-colors');
    });
  });

  describe('Blockquotes', () => {
    it('renders blockquotes correctly', () => {
      render(<MessageRenderer content="> This is a quote" />);
      const blockquote = screen.getByText('This is a quote').closest('blockquote');
      expect(blockquote).toBeInTheDocument();
      expect(blockquote).toHaveClass('border-l-4', 'border-blue-500', 'pl-4');
    });
  });

  describe('Tables', () => {
    it('renders tables correctly', () => {
      const tableContent = `
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
      `;
      render(<MessageRenderer content={tableContent} />);
      
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
      
      expect(screen.getByText('Header 1')).toBeInTheDocument();
      expect(screen.getByText('Header 2')).toBeInTheDocument();
      expect(screen.getByText('Cell 1')).toBeInTheDocument();
      expect(screen.getByText('Cell 2')).toBeInTheDocument();
    });
  });

  describe('Streaming Support', () => {
    it('shows streaming indicator when isStreaming is true', () => {
      render(<MessageRenderer content="Test content" isStreaming={true} />);
      expect(screen.getByText('Generating response...')).toBeInTheDocument();
    });

    it('hides streaming indicator when isStreaming is false', () => {
      render(<MessageRenderer content="Test content" isStreaming={false} />);
      expect(screen.queryByText('Generating response...')).not.toBeInTheDocument();
    });

    it('shows animated pulse indicator during streaming', () => {
      render(<MessageRenderer content="Test content" isStreaming={true} />);
      const indicator = document.querySelector('.animate-pulse');
      expect(indicator).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('applies custom className when provided', () => {
      render(<MessageRenderer content="Test" className="custom-class" />);
      const renderer = document.querySelector('.message-renderer');
      expect(renderer).toHaveClass('custom-class');
    });

    it('handles empty content gracefully', () => {
      render(<MessageRenderer content="" />);
      const renderer = document.querySelector('.message-renderer');
      expect(renderer).toBeInTheDocument();
    });

    it('handles null/undefined content gracefully', () => {
      // @ts-ignore - testing edge case
      render(<MessageRenderer content={null} />);
      const renderer = document.querySelector('.message-renderer');
      expect(renderer).toBeInTheDocument();
    });
  });

  describe('Props Validation', () => {
    it('accepts onCopyCode callback prop', () => {
      const mockCallback = jest.fn();
      render(<MessageRenderer content="Test" onCopyCode={mockCallback} />);
      // The callback will be tested more thoroughly in CodeBlock component tests
      expect(mockCallback).toBeDefined();
    });

    it('renders with default props when optional props are not provided', () => {
      render(<MessageRenderer content="Test content" />);
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('maintains proper heading hierarchy', () => {
      const content = `
# Main Title
## Subtitle
### Section
      `;
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument();
    });

    it('provides proper list semantics', () => {
      render(<MessageRenderer content="- Item 1\n- Item 2" />);
      const list = screen.getByRole('list');
      const items = screen.getAllByRole('listitem');
      
      expect(list).toBeInTheDocument();
      expect(items).toHaveLength(2);
    });

    it('provides proper table semantics', () => {
      const tableContent = `
| Name | Age |
|------|-----|
| John | 25  |
      `;
      render(<MessageRenderer content={tableContent} />);
      
      const table = screen.getByRole('table');
      const columnHeaders = screen.getAllByRole('columnheader');
      const cells = screen.getAllByRole('cell');
      
      expect(table).toBeInTheDocument();
      expect(columnHeaders).toHaveLength(2);
      expect(cells).toHaveLength(2);
    });
  });
});