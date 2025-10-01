import { renderHook, act } from '@testing-library/react';
import { useTouchInteractions, useMobileDetection } from '../useTouchInteractions';

// Mock navigator.vibrate
const mockVibrate = jest.fn();
Object.defineProperty(navigator, 'vibrate', {
  value: mockVibrate,
  writable: true,
});

// Mock window dimensions
const mockWindowDimensions = (width: number, height: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
};

// Mock user agent
const mockUserAgent = (userAgent: string) => {
  Object.defineProperty(navigator, 'userAgent', {
    value: userAgent,
    writable: true,
  });
};

// Mock touch support
const mockTouchSupport = (hasTouch: boolean) => {
  if (hasTouch) {
    Object.defineProperty(window, 'ontouchstart', {
      value: () => {},
      writable: true,
    });
    Object.defineProperty(navigator, 'maxTouchPoints', {
      value: 5,
      writable: true,
    });
  } else {
    delete (window as any).ontouchstart;
    Object.defineProperty(navigator, 'maxTouchPoints', {
      value: 0,
      writable: true,
    });
  }
};

describe('useTouchInteractions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    // Reset DOM
    document.head.innerHTML = '';
    document.body.innerHTML = '';
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initialization', () => {
    it('should initialize with default touch state', () => {
      const { result } = renderHook(() => useTouchInteractions());
      
      expect(result.current.touchState).toEqual({
        isPressed: false,
        isSwiping: false,
        swipeDirection: null,
        isLongPress: false,
        touchPosition: null,
      });
    });

    it('should initialize with custom config', () => {
      const config = {
        enableHapticFeedback: false,
        enableRippleEffect: false,
        rippleColor: 'rgba(255, 0, 0, 0.5)',
        touchFeedbackDuration: 200,
        swipeThreshold: 100,
        longPressDelay: 1000,
      };
      
      const { result } = renderHook(() => useTouchInteractions(config));
      
      // Should not crash and should provide touch handlers
      expect(typeof result.current.getTouchHandlers).toBe('function');
      expect(typeof result.current.getTouchFeedbackStyles).toBe('function');
    });
  });

  describe('Haptic Feedback', () => {
    it('should trigger haptic feedback when enabled', () => {
      const { result } = renderHook(() => useTouchInteractions({
        enableHapticFeedback: true,
      }));
      
      act(() => {
        result.current.triggerHapticFeedback('medium');
      });
      
      expect(mockVibrate).toHaveBeenCalledWith(50);
    });

    it('should not trigger haptic feedback when disabled', () => {
      const { result } = renderHook(() => useTouchInteractions({
        enableHapticFeedback: false,
      }));
      
      act(() => {
        result.current.triggerHapticFeedback('medium');
      });
      
      expect(mockVibrate).not.toHaveBeenCalled();
    });

    it('should handle different haptic feedback intensities', () => {
      const { result } = renderHook(() => useTouchInteractions({
        enableHapticFeedback: true,
      }));
      
      act(() => {
        result.current.triggerHapticFeedback('light');
      });
      expect(mockVibrate).toHaveBeenCalledWith(10);
      
      act(() => {
        result.current.triggerHapticFeedback('heavy');
      });
      expect(mockVibrate).toHaveBeenCalledWith(100);
    });
  });

  describe('Ripple Effect', () => {
    it('should create ripple effect when enabled', () => {
      const { result } = renderHook(() => useTouchInteractions({
        enableRippleEffect: true,
      }));
      
      const mockElement = document.createElement('div');
      document.body.appendChild(mockElement);
      
      // Mock getBoundingClientRect
      mockElement.getBoundingClientRect = jest.fn(() => ({
        left: 0,
        top: 0,
        width: 100,
        height: 100,
        right: 100,
        bottom: 100,
        x: 0,
        y: 0,
        toJSON: () => {},
      }));
      
      act(() => {
        result.current.createRippleEffect(mockElement, 50, 50);
      });
      
      // Should add ripple element
      expect(mockElement.children.length).toBe(1);
      expect(mockElement.style.position).toBe('relative');
      expect(mockElement.style.overflow).toBe('hidden');
      
      // Should add ripple styles to head
      expect(document.head.querySelector('#ripple-styles')).toBeInTheDocument();
    });

    it('should not create ripple effect when disabled', () => {
      const { result } = renderHook(() => useTouchInteractions({
        enableRippleEffect: false,
      }));
      
      const mockElement = document.createElement('div');
      document.body.appendChild(mockElement);
      
      act(() => {
        result.current.createRippleEffect(mockElement, 50, 50);
      });
      
      expect(mockElement.children.length).toBe(0);
    });

    it('should clean up ripple element after animation', () => {
      const { result } = renderHook(() => useTouchInteractions({
        enableRippleEffect: true,
      }));
      
      const mockElement = document.createElement('div');
      document.body.appendChild(mockElement);
      
      mockElement.getBoundingClientRect = jest.fn(() => ({
        left: 0,
        top: 0,
        width: 100,
        height: 100,
        right: 100,
        bottom: 100,
        x: 0,
        y: 0,
        toJSON: () => {},
      }));
      
      act(() => {
        result.current.createRippleEffect(mockElement, 50, 50);
      });
      
      expect(mockElement.children.length).toBe(1);
      
      // Fast forward time to after ripple animation
      act(() => {
        jest.advanceTimersByTime(600);
      });
      
      expect(mockElement.children.length).toBe(0);
    });
  });

  describe('Touch Handlers', () => {
    it('should provide touch event handlers', () => {
      const { result } = renderHook(() => useTouchInteractions());
      
      const handlers = result.current.getTouchHandlers();
      
      expect(handlers).toHaveProperty('onTouchStart');
      expect(handlers).toHaveProperty('onTouchMove');
      expect(handlers).toHaveProperty('onTouchEnd');
      expect(handlers).toHaveProperty('onTouchCancel');
      
      expect(typeof handlers.onTouchStart).toBe('function');
      expect(typeof handlers.onTouchMove).toBe('function');
      expect(typeof handlers.onTouchEnd).toBe('function');
      expect(typeof handlers.onTouchCancel).toBe('function');
    });

    it('should call callbacks when provided', () => {
      const callbacks = {
        onTap: jest.fn(),
        onLongPress: jest.fn(),
        onSwipe: jest.fn(),
        onTouchStart: jest.fn(),
        onTouchEnd: jest.fn(),
      };
      
      const { result } = renderHook(() => useTouchInteractions());
      
      const handlers = result.current.getTouchHandlers(callbacks);
      
      // Mock touch event
      const mockTouchEvent = {
        nativeEvent: {
          touches: [{ clientX: 50, clientY: 50 }],
          changedTouches: [{ clientX: 50, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(mockTouchEvent);
      });
      
      expect(callbacks.onTouchStart).toHaveBeenCalled();
      
      act(() => {
        handlers.onTouchEnd(mockTouchEvent);
      });
      
      expect(callbacks.onTouchEnd).toHaveBeenCalled();
      expect(callbacks.onTap).toHaveBeenCalled();
    });
  });

  describe('Touch State Management', () => {
    it('should update touch state on touch start', () => {
      const { result } = renderHook(() => useTouchInteractions());
      
      const handlers = result.current.getTouchHandlers();
      const mockTouchEvent = {
        nativeEvent: {
          touches: [{ clientX: 50, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(mockTouchEvent);
      });
      
      expect(result.current.touchState.isPressed).toBe(true);
      expect(result.current.touchState.touchPosition).toEqual({ x: 50, y: 50 });
    });

    it('should detect swipe gestures', () => {
      const { result } = renderHook(() => useTouchInteractions({
        swipeThreshold: 50,
      }));
      
      const handlers = result.current.getTouchHandlers();
      
      // Start touch
      const startEvent = {
        nativeEvent: {
          touches: [{ clientX: 0, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(startEvent);
      });
      
      // Move touch (swipe right)
      const moveEvent = {
        nativeEvent: {
          touches: [{ clientX: 100, clientY: 50 }],
        },
      } as any;
      
      act(() => {
        handlers.onTouchMove(moveEvent);
      });
      
      expect(result.current.touchState.isSwiping).toBe(true);
      expect(result.current.touchState.swipeDirection).toBe('right');
    });

    it('should detect long press', () => {
      const { result } = renderHook(() => useTouchInteractions({
        longPressDelay: 500,
      }));
      
      const handlers = result.current.getTouchHandlers();
      const mockTouchEvent = {
        nativeEvent: {
          touches: [{ clientX: 50, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(mockTouchEvent);
      });
      
      expect(result.current.touchState.isLongPress).toBe(false);
      
      // Fast forward time
      act(() => {
        jest.advanceTimersByTime(500);
      });
      
      expect(result.current.touchState.isLongPress).toBe(true);
    });

    it('should cancel long press on movement', () => {
      const { result } = renderHook(() => useTouchInteractions({
        longPressDelay: 500,
      }));
      
      const handlers = result.current.getTouchHandlers();
      
      // Start touch
      const startEvent = {
        nativeEvent: {
          touches: [{ clientX: 50, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(startEvent);
      });
      
      // Move touch (should cancel long press)
      const moveEvent = {
        nativeEvent: {
          touches: [{ clientX: 65, clientY: 50 }], // Move more than 10px
        },
      } as any;
      
      act(() => {
        handlers.onTouchMove(moveEvent);
      });
      
      // Fast forward time
      act(() => {
        jest.advanceTimersByTime(500);
      });
      
      expect(result.current.touchState.isLongPress).toBe(false);
    });
  });

  describe('Touch Feedback Styles', () => {
    it('should provide touch feedback styles', () => {
      const { result } = renderHook(() => useTouchInteractions({
        touchFeedbackDuration: 200,
      }));
      
      const styles = result.current.getTouchFeedbackStyles();
      
      expect(styles).toEqual({
        transform: 'scale(1)',
        transition: 'transform 200ms ease-out',
        userSelect: 'none',
        WebkitUserSelect: 'none',
        WebkitTouchCallout: 'none',
        WebkitTapHighlightColor: 'transparent',
      });
    });

    it('should change styles when pressed', () => {
      const { result } = renderHook(() => useTouchInteractions());
      
      const handlers = result.current.getTouchHandlers();
      const mockTouchEvent = {
        nativeEvent: {
          touches: [{ clientX: 50, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(mockTouchEvent);
      });
      
      const styles = result.current.getTouchFeedbackStyles();
      expect(styles.transform).toBe('scale(0.98)');
    });
  });

  describe('Cleanup', () => {
    it('should cleanup timers on unmount', () => {
      const { result, unmount } = renderHook(() => useTouchInteractions());
      
      const handlers = result.current.getTouchHandlers();
      const mockTouchEvent = {
        nativeEvent: {
          touches: [{ clientX: 50, clientY: 50 }],
          currentTarget: document.createElement('div'),
        },
      } as any;
      
      act(() => {
        handlers.onTouchStart(mockTouchEvent);
      });
      
      // Should not throw when unmounting with active timers
      expect(() => unmount()).not.toThrow();
    });
  });
});

describe('useMobileDetection', () => {
  beforeEach(() => {
    // Reset to desktop defaults
    mockWindowDimensions(1024, 768);
    mockUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    mockTouchSupport(false);
  });

  describe('Mobile Detection', () => {
    it('should detect mobile by user agent', () => {
      mockUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)');
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.isMobile).toBe(true);
    });

    it('should detect mobile by screen width', () => {
      mockWindowDimensions(375, 667); // iPhone dimensions
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.isMobile).toBe(true);
    });

    it('should detect desktop', () => {
      mockWindowDimensions(1920, 1080);
      mockUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.isMobile).toBe(false);
    });
  });

  describe('Touch Detection', () => {
    it('should detect touch support', () => {
      mockTouchSupport(true);
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.hasTouch).toBe(true);
    });

    it('should detect no touch support', () => {
      mockTouchSupport(false);
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.hasTouch).toBe(false);
    });
  });

  describe('Orientation Detection', () => {
    it('should detect portrait orientation', () => {
      mockWindowDimensions(375, 667); // Portrait
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.orientation).toBe('portrait');
    });

    it('should detect landscape orientation', () => {
      mockWindowDimensions(667, 375); // Landscape
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.orientation).toBe('landscape');
    });

    it('should update orientation on window resize', () => {
      mockWindowDimensions(375, 667); // Start portrait
      
      const { result } = renderHook(() => useMobileDetection());
      
      expect(result.current.orientation).toBe('portrait');
      
      // Change to landscape
      act(() => {
        mockWindowDimensions(667, 375);
        window.dispatchEvent(new Event('resize'));
      });
      
      expect(result.current.orientation).toBe('landscape');
    });
  });

  describe('Event Listeners', () => {
    it('should add and remove event listeners', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      
      const { unmount } = renderHook(() => useMobileDetection());
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('orientationchange', expect.any(Function));
      
      unmount();
      
      expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('orientationchange', expect.any(Function));
      
      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });
  });
});