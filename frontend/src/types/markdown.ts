// Base TypeScript interfaces for enhanced message rendering

export interface MessageRendererProps {
  content: string;
  isStreaming?: boolean;
  onCopyCode?: (code: string) => void;
  className?: string;
}

export interface CodeBlockProps {
  children: string;
  language?: string;
  inline?: boolean;
  showCopyButton?: boolean;
  onCopy?: (code: string) => void;
}

export interface StreamingRendererProps {
  content: string;
  isComplete: boolean;
  onContentUpdate?: (renderedContent: string) => void;
}

export interface StreamingState {
  processedContent: string;
  pendingContent: string;
  isProcessing: boolean;
}

export interface EnhancedMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  renderedContent?: string;
  hasCodeBlocks?: boolean;
  codeBlocks?: CodeBlock[];
  formattingMetadata?: FormattingMetadata;
}

export interface CodeBlock {
  id: string;
  language: string;
  code: string;
  startLine?: number;
  endLine?: number;
}

export interface FormattingMetadata {
  hasHeaders: boolean;
  hasLists: boolean;
  hasTables: boolean;
  hasLinks: boolean;
  hasBlockquotes: boolean;
  estimatedReadTime: number;
}

export interface MarkdownError {
  type: 'parsing' | 'rendering' | 'syntax-highlighting';
  message: string;
  line?: number;
  column?: number;
  recoverable: boolean;
}

export interface StreamingError {
  type: 'incomplete-markdown' | 'malformed-code-block' | 'parsing-timeout';
  content: string;
  position: number;
  recovery: 'retry' | 'fallback' | 'skip';
}

export interface MarkdownTheme {
  typography: {
    headings: {
      h1: string;
      h2: string;
      h3: string;
      h4: string;
      h5: string;
      h6: string;
    };
    paragraph: string;
    list: string;
    listItem: string;
    blockquote: string;
    code: string;
    inlineCode: string;
  };
  colors: {
    text: string;
    textSecondary: string;
    border: string;
    background: string;
    codeBackground: string;
    linkColor: string;
    linkHover: string;
  };
  spacing: {
    paragraph: string;
    list: string;
    blockquote: string;
    codeBlock: string;
  };
}

// Component prop interfaces for custom markdown components
export interface HeadingProps {
  level: number;
  children: React.ReactNode;
  className?: string;
}

export interface ParagraphProps {
  children: React.ReactNode;
  className?: string;
}

export interface ListProps {
  ordered?: boolean;
  children: React.ReactNode;
  className?: string;
}

export interface ListItemProps {
  children: React.ReactNode;
  className?: string;
}

export interface BlockquoteProps {
  children: React.ReactNode;
  className?: string;
}

export interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export interface LinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

export interface CodeProps {
  inline?: boolean;
  className?: string;
  children: React.ReactNode;
}

export interface PreProps {
  children: React.ReactNode;
  className?: string;
}