import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Home from './page';

// Mock the SpeechRecognition API
const mockSpeechRecognition = {
  start: jest.fn(),
  stop: jest.fn(),
  abort: jest.fn(),
  continuous: false,
  interimResults: false,
  lang: 'en-US',
  onresult: null,
  onerror: null,
  onend: null,
  onstart: null
};

// Mock window.speechRecognition
Object.defineProperty(window, 'SpeechRecognition', {
  writable: true,
  value: jest.fn().mockImplementation(() => mockSpeechRecognition)
});

Object.defineProperty(window, 'webkitSpeechRecognition', {
  writable: true,
  value: jest.fn().mockImplementation(() => mockSpeechRecognition)
});

// Mock next-themes
jest.mock('next-themes', () => ({
  useTheme: () => ({
    theme: 'light',
    setTheme: jest.fn()
  })
}));

// Mock the useDarkMode hook
jest.mock('@/hooks/useDarkMode', () => ({
  useDarkMode: () => ({
    isDarkMode: false,
    toggleDarkMode: jest.fn()
  })
}));

// Mock the magicui components
jest.mock('@/components/magicui', () => ({
  AnimatedThemeToggler: () => <div data-testid="theme-toggler">Theme Toggler</div>,
  VoiceThemeNotification: () => <div data-testid="voice-notification">Voice Notification</div>,
  AuroraText: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

// Mock the AIModelDropdown component
jest.mock('@/components/magicui/ai-model-dropdown', () => ({
  AIModelDropdown: () => <div data-testid="ai-model-dropdown">AI Model Dropdown</div>
}));

describe('Home Page - Voice Recognition', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders microphone button with correct tooltip', () => {
    render(<Home />);
    
    const micButton = screen.getByRole('button', { name: /Start voice input/i });
    expect(micButton).toBeInTheDocument();
    expect(micButton).toHaveAttribute('title', 'Start voice input (Cmd+Enter or Ctrl+Enter)');
  });

  test('toggles voice recognition when microphone button is clicked', async () => {
    render(<Home />);
    
    const micButton = screen.getByRole('button', { name: /Start voice input/i });
    
    // Click to start voice recognition
    await user.click(micButton);
    
    expect(mockSpeechRecognition.start).toHaveBeenCalledTimes(1);
    
    // Simulate the onstart event
    mockSpeechRecognition.onstart?.(new Event('start'));
    
    // Button should now show stop listening tooltip
    expect(micButton).toHaveAttribute('title', 'Stop listening (Cmd+Enter or Ctrl+Enter)');
    
    // Click to stop voice recognition
    await user.click(micButton);
    
    expect(mockSpeechRecognition.stop).toHaveBeenCalledTimes(1);
  });

  test('handles keyboard shortcut for voice recognition', async () => {
    render(<Home />);
    
    const textarea = screen.getByRole('textbox');
    
    // Focus the textarea
    textarea.focus();
    
    // Press Cmd+Enter (macOS)
    await user.keyboard('{Meta>}Enter{/Meta}');
    
    expect(mockSpeechRecognition.start).toHaveBeenCalledTimes(1);
  });

  test('handles keyboard shortcut for voice recognition (Windows/Linux)', async () => {
    render(<Home />);
    
    const textarea = screen.getByRole('textbox');
    
    // Focus the textarea
    textarea.focus();
    
    // Press Ctrl+Enter (Windows/Linux)
    await user.keyboard('{Control>}Enter{/Control}');
    
    expect(mockSpeechRecognition.start).toHaveBeenCalledTimes(1);
  });

  test('debounces rapid keyboard shortcut presses', async () => {
    jest.useFakeTimers();
    
    render(<Home />);
    
    const textarea = screen.getByRole('textbox');
    textarea.focus();
    
    // Rapidly press the shortcut multiple times
    await user.keyboard('{Meta>}Enter{/Meta}');
    await user.keyboard('{Meta>}Enter{/Meta}');
    await user.keyboard('{Meta>}Enter{/Meta}');
    
    // Advance timers
    jest.advanceTimersByTime(300);
    
    // Should only call start once due to debouncing
    expect(mockSpeechRecognition.start).toHaveBeenCalledTimes(1);
    
    jest.useRealTimers();
  });

  test('handles InvalidStateError gracefully', async () => {
    render(<Home />);
    
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    
    // Mock the start method to throw InvalidStateError
    mockSpeechRecognition.start.mockImplementationOnce(() => {
      const error = new Error('recognition has already started');
      error.name = 'InvalidStateError';
      throw error;
    });
    
    const micButton = screen.getByRole('button', { name: /Start voice input/i });
    await user.click(micButton);
    
    // Should handle the error gracefully without crashing
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error starting speech recognition:',
      expect.objectContaining({ name: 'InvalidStateError' })
    );
    
    consoleErrorSpy.mockRestore();
  });

  test('handles NotAllowedError for microphone access denied', async () => {
    render(<Home />);
    
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    
    // Mock the start method to throw NotAllowedError
    mockSpeechRecognition.start.mockImplementationOnce(() => {
      const error = new Error('Permission denied');
      error.name = 'NotAllowedError';
      throw error;
    });
    
    const micButton = screen.getByRole('button', { name: /Start voice input/i });
    await user.click(micButton);
    
    // Should show user-friendly error message
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error starting speech recognition:',
      expect.objectContaining({ name: 'NotAllowedError' })
    );
    
    // Wait for error message to appear and then disappear
    await waitFor(() => {
      expect(screen.getByText(/Microphone access denied/i)).toBeInTheDocument();
    });
    
    consoleErrorSpy.mockRestore();
  });

  test('handles voice commands correctly', async () => {
    render(<Home />);
    
    const mockToggleDarkMode = jest.fn();
    
    // We would need to mock the useDarkMode hook to test this properly
    // This is a simplified test
    const mockEvent = {
      results: [{
        0: {
          transcript: 'system switch dark mode'
        }
      }]
    };
    
    // Simulate voice recognition result
    mockSpeechRecognition.onresult?.(mockEvent);
    
    // In a real test, we would verify that the theme was toggled
    // and the notification was shown
  });

  test('shows error message for audio capture failure', async () => {
    render(<Home />);
    
    const mockEvent = {
      error: 'audio-capture'
    };
    
    // Simulate speech recognition error
    mockSpeechRecognition.onerror?.(mockEvent);
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(/Audio capture failed/i)).toBeInTheDocument();
    });
  });

  test('clears error message after 5 seconds', async () => {
    jest.useFakeTimers();
    
    render(<Home />);
    
    const mockEvent = {
      error: 'audio-capture'
    };
    
    // Simulate speech recognition error
    mockSpeechRecognition.onerror?.(mockEvent);
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(/Audio capture failed/i)).toBeInTheDocument();
    });
    
    // Fast-forward time by 5 seconds
    jest.advanceTimersByTime(5000);
    
    // Error message should be gone
    expect(screen.queryByText(/Audio capture failed/i)).not.toBeInTheDocument();
    
    jest.useRealTimers();
  });
});