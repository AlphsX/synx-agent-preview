import { render, screen, fireEvent } from '@testing-library/react';
import { AnimatedThemeToggler } from './animated-theme-toggler';

// Mock the useDarkMode hook
jest.mock('@/hooks/useDarkMode', () => ({
  useDarkMode: () => ({
    isDarkMode: false,
    toggleDarkMode: jest.fn(),
  }),
}));

describe('AnimatedThemeToggler', () => {
  it('renders correctly in light mode', () => {
    const toggleDarkMode = jest.fn();
    render(<AnimatedThemeToggler isDarkMode={false} toggleDarkMode={toggleDarkMode} />);
    
    // Check if the component renders
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('renders correctly in dark mode', () => {
    const toggleDarkMode = jest.fn();
    render(<AnimatedThemeToggler isDarkMode={true} toggleDarkMode={toggleDarkMode} />);
    
    // Check if the component renders
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('calls toggleDarkMode when clicked', () => {
    const toggleDarkMode = jest.fn();
    render(<AnimatedThemeToggler isDarkMode={false} toggleDarkMode={toggleDarkMode} />);
    
    // Click the button
    fireEvent.click(screen.getByRole('button'));
    
    // Check if toggleDarkMode was called
    expect(toggleDarkMode).toHaveBeenCalledTimes(1);
  });

  it('has proper aria-label for accessibility', () => {
    const toggleDarkMode = jest.fn();
    
    // Test light mode label
    const { rerender } = render(<AnimatedThemeToggler isDarkMode={false} toggleDarkMode={toggleDarkMode} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Switch to dark mode');
    
    // Test dark mode label
    rerender(<AnimatedThemeToggler isDarkMode={true} toggleDarkMode={toggleDarkMode} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Switch to light mode');
  });
});