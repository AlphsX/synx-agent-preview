import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CodeBlock } from '../CodeBlock';

// Mock the syntax highlighter to avoid issues in test environment
jest.mock('react-syntax-highlighter', () => ({
  Prism: ({ children, language, ...props }: any) => (
    <pre data-testid="syntax-highlighter" data-language={language} {...props}>
      <code>{children}</code>
    </pre>
  )
}));

jest.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  oneDark: {},
  oneLight: {}
}));

// Mock the markdown utilities
jest.mock('@/lib/markdown-utils', () => ({
  detectLanguage: jest.fn((lang: string) => {
    const langMap: Record<string, string> = {
      'js': 'javascript',
      'ts': 'typescript',
      'py': 'python',
      '': 'plaintext'
    };
    return langMap[lang] || lang || 'plaintext';
  })
}));

// Mock clipboard API
const mockClipboard = {
  writeText: jest.fn()
};

Object.assign(navigator, {
  clipboard: mockClipboard
});

// Mock window.isSecureContext
Object.defineProperty(window, 'isSecureContext', {
  writable: true,
  value: true
});

describe('CodeBlock', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockClipboard.writeText.mockResolvedValue(undefined);
  });

  describe('Basic Rendering', () => {
    it('renders inline code correctly', () => {
      render(<CodeBlock inline={true}>const x = 5;</CodeBlock>);
      const codeElement = screen.getByText('const x = 5;');
      expect(codeElement.tagName).toBe('CODE');
      expect(codeElement).toHaveClass('bg-gray-100', 'dark:bg-gray-800');
    });

    it('renders block code correctly', () => {
      render(<CodeBlock>const x = 5;</CodeBlock>);
      expect(screen.getByTestId('syntax-highlighter')).toBeInTheDocument();
      expect(screen.getByText('const x = 5;')).toBeInTheDocument();
    });

    it('renders code with specified language', () => {
      render(<CodeBlock language="javascript">console.log('hello');</CodeBlock>);
      const highlighter = screen.getByTestId('syntax-highlighter');
      expect(highlighter).toHaveAttribute('data-language', 'javascript');
    });

    it('detects language when not specified', () => {
      render(<CodeBlock>print('hello')</CodeBlock>);
      const highlighter = screen.getByTestId('syntax-highlighter');
      expect(highlighter).toHaveAttribute('data-language', 'plaintext');
    });
  });

  describe('Language Detection and Display', () => {
    it('shows language badge for recognized languages', () => {
      render(<CodeBlock language="python">print('hello')</CodeBlock>);
      expect(screen.getByText('python')).toBeInTheDocument();
    });

    it('does not show language badge for plaintext', () => {
      render(<CodeBlock language="plaintext">some text</CodeBlock>);
      expect(screen.queryByText('plaintext')).not.toBeInTheDocument();
    });

    it('does not show language badge for text', () => {
      render(<CodeBlock language="text">some text</CodeBlock>);
      expect(screen.queryByText('text')).not.toBeInTheDocument();
    });

    it('handles language aliases correctly', () => {
      render(<CodeBlock language="js">console.log('test');</CodeBlock>);
      const highlighter = screen.getByTestId('syntax-highlighter');
      expect(highlighter).toHaveAttribute('data-language', 'javascript');
    });
  });

  describe('Copy Functionality', () => {
    it('shows copy button by default', () => {
      render(<CodeBlock>test code</CodeBlock>);
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      expect(copyButton).toBeInTheDocument();
    });

    it('hides copy button when showCopyButton is false', () => {
      render(<CodeBlock showCopyButton={false}>test code</CodeBlock>);
      const copyButton = screen.queryByLabelText('Copy code to clipboard');
      expect(copyButton).not.toBeInTheDocument();
    });

    it('copies code to clipboard when copy button is clicked', async () => {
      const testCode = 'const x = 5;\nconsole.log(x);';
      render(<CodeBlock>{testCode}</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith(testCode);
      });
    });

    it('shows success state after successful copy', async () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Copied to clipboard')).toBeInTheDocument();
      });
    });

    it('calls onCopy callback when provided', async () => {
      const mockOnCopy = jest.fn();
      const testCode = 'test code';
      
      render(<CodeBlock onCopy={mockOnCopy}>{testCode}</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(mockOnCopy).toHaveBeenCalledWith(testCode);
      });
    });

    it('handles copy failure gracefully', async () => {
      mockClipboard.writeText.mockRejectedValue(new Error('Copy failed'));
      
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(screen.getByText('Copy failed')).toBeInTheDocument();
      });
    });

    it('resets copy state after timeout', async () => {
      jest.useFakeTimers();
      
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Copied to clipboard')).toBeInTheDocument();
      });
      
      // Fast-forward time
      jest.advanceTimersByTime(2000);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Copy code to clipboard')).toBeInTheDocument();
      });
      
      jest.useRealTimers();
    });
  });

  describe('Fallback Copy Mechanism', () => {
    beforeEach(() => {
      // Mock the fallback scenario (no clipboard API or insecure context)
      Object.defineProperty(window, 'isSecureContext', {
        writable: true,
        value: false
      });
      
      // Mock document.execCommand
      document.execCommand = jest.fn().mockReturnValue(true);
    });

    afterEach(() => {
      Object.defineProperty(window, 'isSecureContext', {
        writable: true,
        value: true
      });
    });

    it('uses fallback copy method when clipboard API is not available', async () => {
      // Remove clipboard API
      const originalClipboard = navigator.clipboard;
      // @ts-ignore
      delete navigator.clipboard;
      
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(document.execCommand).toHaveBeenCalledWith('copy');
      });
      
      // Restore clipboard API
      Object.defineProperty(navigator, 'clipboard', {
        value: originalClipboard,
        writable: true
      });
    });
  });

  describe('Responsive Design', () => {
    it('shows mobile copy button on small screens', () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      // The mobile button should be present but hidden on larger screens
      const mobileButton = screen.getByText('Copy');
      expect(mobileButton).toBeInTheDocument();
      expect(mobileButton).toHaveClass('md:hidden');
    });

    it('mobile copy button works correctly', async () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const mobileButton = screen.getByText('Copy');
      fireEvent.click(mobileButton);
      
      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith('test code');
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels for copy button', () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      expect(copyButton).toHaveAttribute('aria-label', 'Copy code to clipboard');
    });

    it('updates ARIA label when copied', async () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Copied to clipboard')).toBeInTheDocument();
      });
    });

    it('provides proper title attributes', () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      expect(copyButton).toHaveAttribute('title', 'Copy code');
    });

    it('supports keyboard navigation', () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      expect(copyButton).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-blue-500');
    });
  });

  describe('Content Processing', () => {
    it('removes trailing newlines from code content', () => {
      const codeWithNewline = 'console.log("test");\n';
      render(<CodeBlock>{codeWithNewline}</CodeBlock>);
      
      const copyButton = screen.getByLabelText('Copy code to clipboard');
      fireEvent.click(copyButton);
      
      expect(mockClipboard.writeText).toHaveBeenCalledWith('console.log("test");');
    });

    it('handles empty code content', () => {
      render(<CodeBlock></CodeBlock>);
      expect(screen.getByTestId('syntax-highlighter')).toBeInTheDocument();
    });

    it('handles multiline code correctly', () => {
      const multilineCode = `function test() {
  console.log('hello');
  return true;
}`;
      
      render(<CodeBlock>{multilineCode}</CodeBlock>);
      expect(screen.getByText(multilineCode)).toBeInTheDocument();
    });
  });

  describe('Theme Integration', () => {
    it('applies correct CSS classes for dark mode support', () => {
      render(<CodeBlock>test code</CodeBlock>);
      
      const container = document.querySelector('.border-gray-200.dark\\:border-gray-700');
      expect(container).toBeInTheDocument();
    });

    it('applies correct styling to language badge', () => {
      render(<CodeBlock language="javascript">test code</CodeBlock>);
      
      const badge = screen.getByText('javascript');
      expect(badge).toHaveClass('bg-gray-200', 'dark:bg-gray-600');
    });
  });
});