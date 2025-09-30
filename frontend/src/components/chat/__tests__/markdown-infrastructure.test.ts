// Basic tests to verify markdown infrastructure setup

import { 
  detectLanguage, 
  validateMarkdownContent, 
  extractCodeBlocks,
  analyzeMarkdownFeatures,
  estimateReadingTime 
} from '@/lib/markdown-utils';
import { MarkdownError } from '@/types/markdown';

describe('Markdown Infrastructure', () => {
  describe('Language Detection', () => {
    test('should detect common languages correctly', () => {
      expect(detectLanguage('javascript')).toBe('javascript');
      expect(detectLanguage('js')).toBe('javascript');
      expect(detectLanguage('typescript')).toBe('typescript');
      expect(detectLanguage('ts')).toBe('typescript');
      expect(detectLanguage('python')).toBe('python');
      expect(detectLanguage('py')).toBe('python');
    });

    test('should fallback to plaintext for unknown languages', () => {
      expect(detectLanguage('unknown-lang')).toBe('plaintext');
      expect(detectLanguage('')).toBe('plaintext');
    });
  });

  describe('Content Validation', () => {
    test('should detect unclosed code blocks', () => {
      const content = '```javascript\nconsole.log("test");';
      const errors = validateMarkdownContent(content);
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('parsing');
      expect(errors[0].message).toContain('Unclosed code block');
    });

    test('should detect invalid header levels', () => {
      const content = '####### Invalid header';
      const errors = validateMarkdownContent(content);
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('parsing');
      expect(errors[0].message).toContain('Invalid header level');
    });

    test('should return no errors for valid content', () => {
      const content = '# Header\n\nSome text with `inline code`.\n\n```javascript\nconsole.log("test");\n```';
      const errors = validateMarkdownContent(content);
      expect(errors).toHaveLength(0);
    });
  });

  describe('Code Block Extraction', () => {
    test('should extract code blocks correctly', () => {
      const content = '# Title\n\n```javascript\nconsole.log("hello");\n```\n\nSome text\n\n```python\nprint("world")\n```';
      const blocks = extractCodeBlocks(content);
      
      expect(blocks).toHaveLength(2);
      expect(blocks[0].language).toBe('javascript');
      expect(blocks[0].code).toBe('console.log("hello");');
      expect(blocks[1].language).toBe('python');
      expect(blocks[1].code).toBe('print("world")');
    });
  });

  describe('Feature Analysis', () => {
    test('should detect markdown features correctly', () => {
      const content = '# Header\n\n- List item\n\n> Blockquote\n\n[Link](url)\n\n```code```\n\n`inline`';
      const features = analyzeMarkdownFeatures(content);
      
      expect(features.hasHeaders).toBe(true);
      expect(features.hasLists).toBe(true);
      expect(features.hasBlockquotes).toBe(true);
      expect(features.hasLinks).toBe(true);
      expect(features.hasCodeBlocks).toBe(true);
      expect(features.hasInlineCode).toBe(true);
    });
  });

  describe('Reading Time Estimation', () => {
    test('should estimate reading time correctly', () => {
      const shortText = 'Short text';
      const longText = 'word '.repeat(200); // 200 words
      
      expect(estimateReadingTime(shortText)).toBe(1);
      expect(estimateReadingTime(longText)).toBe(1);
    });
  });
});

// Test that required packages are available
describe('Package Dependencies', () => {
  test('should have react-markdown available', async () => {
    const ReactMarkdown = await import('react-markdown');
    expect(ReactMarkdown.default).toBeDefined();
  });

  test('should have remark-gfm available', async () => {
    const remarkGfm = await import('remark-gfm');
    expect(remarkGfm.default).toBeDefined();
  });

  test('should have react-syntax-highlighter available', async () => {
    const { Prism } = await import('react-syntax-highlighter');
    expect(Prism).toBeDefined();
  });

  test('should have prism-react-renderer available', async () => {
    const prismRenderer = await import('prism-react-renderer');
    expect(prismRenderer).toBeDefined();
  });
});