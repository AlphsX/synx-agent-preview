// Markdown processing configuration constants

import { MarkdownTheme } from '@/types/markdown';

// Default markdown theme configuration
export const DEFAULT_MARKDOWN_THEME: MarkdownTheme = {
  typography: {
    headings: {
      h1: 'text-3xl font-bold mb-4 mt-6 text-gray-900 dark:text-gray-100',
      h2: 'text-2xl font-semibold mb-3 mt-5 text-gray-900 dark:text-gray-100',
      h3: 'text-xl font-semibold mb-2 mt-4 text-gray-900 dark:text-gray-100',
      h4: 'text-lg font-medium mb-2 mt-3 text-gray-900 dark:text-gray-100',
      h5: 'text-base font-medium mb-1 mt-2 text-gray-900 dark:text-gray-100',
      h6: 'text-sm font-medium mb-1 mt-2 text-gray-700 dark:text-gray-300'
    },
    paragraph: 'mb-4 text-gray-700 dark:text-gray-300 leading-relaxed',
    list: 'mb-4 space-y-1',
    listItem: 'text-gray-700 dark:text-gray-300',
    blockquote: 'border-l-4 border-blue-500 pl-4 py-2 mb-4 bg-blue-50 dark:bg-blue-900/20 text-gray-700 dark:text-gray-300 italic',
    code: 'bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4 overflow-x-auto',
    inlineCode: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 px-1.5 py-0.5 rounded text-sm font-mono'
  },
  colors: {
    text: 'text-gray-900 dark:text-gray-100',
    textSecondary: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-700',
    background: 'bg-white dark:bg-gray-900',
    codeBackground: 'bg-gray-50 dark:bg-gray-800',
    linkColor: 'text-blue-600 dark:text-blue-400',
    linkHover: 'text-blue-800 dark:text-blue-300'
  },
  spacing: {
    paragraph: 'mb-4',
    list: 'mb-4',
    blockquote: 'mb-4',
    codeBlock: 'mb-4'
  }
};

// Streaming configuration
export const STREAMING_CONFIG = {
  DEBOUNCE_DELAY: 100, // ms
  MAX_BUFFER_SIZE: 10000, // characters
  PARSING_TIMEOUT: 5000, // ms
  UPDATE_INTERVAL: 50 // ms
};

// Error recovery configuration
export const ERROR_RECOVERY_CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000, // ms
  FALLBACK_TO_PLAIN_TEXT: true,
  LOG_ERRORS: true
};

// Performance configuration
export const PERFORMANCE_CONFIG = {
  LAZY_LOAD_THRESHOLD: 1000, // characters
  VIRTUALIZATION_THRESHOLD: 5000, // characters
  MEMOIZATION_ENABLED: true,
  SYNTAX_HIGHLIGHTING_DELAY: 0 // ms - 0 for immediate, >0 for delayed
};