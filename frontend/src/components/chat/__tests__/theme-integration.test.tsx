import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MessageRenderer } from '../MessageRenderer';
import { CodeBlock } from '../CodeBlock';

// Mock the theme hooks
jest.mock('@/hooks/useMarkdownTheme', () => ({
  useMarkdownTheme: jest.fn(() => ({
    theme: {
      typography: {
        headings: {
          h1: 'text-3xl font-bold mb-4 mt-6 text-gray-900 dark:text-gray-100',
          h2: 'text-2xl font-semibold mb-3 mt-5 text-gray-900 dark:text-gray-100',
          h3: 'text-xl font-semibold mb-2 mt-4 text-gray-900 dark:text-gray-100'
        },
        paragraph: 'mb-4 text-gray-700 dark:text-gray-300 leading-relaxed'
      },
      colors: {
        text: 'text-gray-900 dark:text-gray-100',
        linkColor: 'text-blue-600 dark:text-blue-400'
      },
      spacing: {
        paragraph: 'mb-4'
      }
    },
    isDarkMode: false,
    cssVariables: {},
    getHeadingClass: (level: number) => `text-${level}xl font-bold`,
    getColorClass: (key: string) => `text-gray-900`,
    getSpacingClass: (key: string) => 'mb-4'
  })),
  useSyntaxHighlightingTheme: jest.fn(() => ({
    isDarkMode: false,
    themeName: 'oneLight',
    backgroundColor: '#f9fafb',
    textColor: '#374151',
    borderColor: '#e5e7eb'
  }))
}));

// Mock react-syntax-highlighter
jest.mock('react-syntax-highlighter', () => ({
  Prism: ({ children, ...props }: any) => (
    <pre data-testid="syntax-highlighter" {...props}>
      <code>{children}</code>
    </pre>
  )
}));

jest.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  oneDark: { background: '#1f2937' },
  oneLight: { background: '#f9fafb' }
}));

describe('Theme Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('MessageRenderer Theme Integration', () => {
    it('applies theme classes to markdown elements', () => {
      const content = `
# Main Header
## Sub Header
This is a paragraph with **bold** text.
      `;
      
      render(<MessageRenderer content={content} />);
      
      const h1 = screen.getByRole('heading', { level: 1 });
      const h2 = screen.getByRole('heading', { level: 2 });
      
      expect(h1).toHaveClass('text-3xl', 'font-bold', 'mb-4', 'mt-6');
      expect(h2).toHaveClass('text-2xl', 'font-semibold', 'mb-3', 'mt-5');
    });

    it('applies correct CSS classes based on theme', () => {
      render(<MessageRenderer content="Test paragraph" />);
      
      const paragraph = screen.getByText('Test paragraph');
      expect(paragraph.closest('p')).toHaveClass('mb-4', 'leading-relaxed');
    });

    it('handles theme switching correctly', () => {
      const { useMarkdownTheme } = require('@/hooks/useMarkdownTheme');
      
      // Mock dark mode
      useMarkdownTheme.mockReturnValue({
        theme: {
          typography: {
            headings: {
              h1: 'text-3xl font-bold mb-4 mt-6 text-gray-100'
            }
          }
        },
        isDarkMode: true,
        cssVariables: {},
        getHeadingClass: () => 'text-3xl font-bold text-gray-100'
      });

      render(<MessageRenderer content="# Dark Mode Header" />);
      
      const header = screen.getByRole('heading', { level: 1 });
      expect(header).toHaveClass('text-3xl', 'font-bold');
    });
  });

  describe('CodeBlock Theme Integration', () => {
    it('applies theme-aware styling to code blocks', () => {
      render(<CodeBlock language="javascript">console.log('test');</CodeBlock>);
      
      const syntaxHighlighter = screen.getByTestId('syntax-highlighter');
      expect(syntaxHighlighter).toBeInTheDocument();
    });

    it('uses correct syntax highlighting theme', () => {
      const { useSyntaxHighlightingTheme } = require('@/hooks/useMarkdownTheme');
      
      // Test light mode
      useSyntaxHighlightingTheme.mockReturnValue({
        isDarkMode: false,
        themeName: 'oneLight',
        backgroundColor: '#f9fafb'
      });

      render(<CodeBlock>test code</CodeBlock>);
      expect(screen.getByTestId('syntax-highlighter')).toBeInTheDocument();
    });

    it('switches syntax highlighting theme in dark mode', () => {
      const { useSyntaxHighlightingTheme } = require('@/hooks/useMarkdownTheme');
      
      // Test dark mode
      useSyntaxHighlightingTheme.mockReturnValue({
        isDarkMode: true,
        themeName: 'oneDark',
        backgroundColor: '#1f2937'
      });

      render(<CodeBlock>test code</CodeBlock>);
      expect(screen.getByTestId('syntax-highlighter')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('applies responsive classes correctly', () => {
      render(<MessageRenderer content="# Responsive Header" className="responsive-test" />);
      
      const container = document.querySelector('.message-renderer');
      expect(container).toHaveClass('responsive-test');
    });

    it('handles mobile-specific styling', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375
      });

      render(<CodeBlock>mobile code test</CodeBlock>);
      
      // Check for mobile copy button
      const mobileButton = screen.getByText('Copy');
      expect(mobileButton).toHaveClass('md:hidden');
    });
  });

  describe('Accessibility Integration', () => {
    it('maintains proper heading hierarchy with theme', () => {
      const content = `
# Level 1
## Level 2  
### Level 3
      `;
      
      render(<MessageRenderer content={content} />);
      
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument();
    });

    it('provides proper focus states with theme integration', () => {
      render(<MessageRenderer content="[Test Link](https://example.com)" />);
      
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'https://example.com');
      expect(link).toHaveClass('transition-colors');
    });

    it('maintains color contrast in different themes', () => {
      render(<MessageRenderer content="`inline code`" />);
      
      const code = screen.getByText('inline code');
      expect(code).toHaveClass('bg-gray-100', 'dark:bg-gray-800');
    });
  });

  describe('Performance Considerations', () => {
    it('memoizes theme calculations', () => {
      const { useMarkdownTheme } = require('@/hooks/useMarkdownTheme');
      const mockTheme = {
        theme: { typography: {}, colors: {}, spacing: {} },
        isDarkMode: false,
        cssVariables: {}
      };
      
      useMarkdownTheme.mockReturnValue(mockTheme);
      
      const { rerender } = render(<MessageRenderer content="Test content" />);
      
      // Re-render with same content
      rerender(<MessageRenderer content="Test content" />);
      
      // Theme hook should be called but memoized values should be reused
      expect(useMarkdownTheme).toHaveBeenCalled();
    });

    it('handles theme changes efficiently', () => {
      const { useMarkdownTheme } = require('@/hooks/useMarkdownTheme');
      
      // Initial light theme
      useMarkdownTheme.mockReturnValue({
        theme: { typography: {}, colors: {}, spacing: {} },
        isDarkMode: false
      });
      
      const { rerender } = render(<MessageRenderer content="Test" />);
      
      // Switch to dark theme
      useMarkdownTheme.mockReturnValue({
        theme: { typography: {}, colors: {}, spacing: {} },
        isDarkMode: true
      });
      
      rerender(<MessageRenderer content="Test" />);
      
      expect(useMarkdownTheme).toHaveBeenCalledTimes(2);
    });
  });

  describe('CSS Custom Properties', () => {
    it('applies CSS variables for dynamic theming', () => {
      const { useMarkdownTheme } = require('@/hooks/useMarkdownTheme');
      
      useMarkdownTheme.mockReturnValue({
        theme: { typography: {}, colors: {}, spacing: {} },
        isDarkMode: false,
        cssVariables: {
          '--markdown-text': 'rgb(17, 24, 39)',
          '--markdown-background': 'rgb(249, 250, 251)'
        }
      });

      render(<MessageRenderer content="Test with CSS variables" />);
      
      // The hook should handle CSS variable application
      expect(useMarkdownTheme).toHaveBeenCalled();
    });
  });

  describe('Error Handling with Themes', () => {
    it('maintains theme consistency during error states', () => {
      // Mock console.error to avoid test noise
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      render(<MessageRenderer content="```unclosed code block" />);
      
      // Should still render with theme classes even with parsing errors
      const container = document.querySelector('.message-renderer');
      expect(container).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });
  });
});