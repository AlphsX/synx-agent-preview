/**
 * Browser Test Utilities
 * Helper functions to test and verify browser detection
 */

import { detectBrowser, getSupportedBrowsers } from './browserDetection';

export interface BrowserTestResult {
  browserName: string;
  isSupported: boolean;
  isDetectedCorrectly: boolean;
  expectedBrowsers: string[];
  testPassed: boolean;
}

// Test user agents for different browsers
export const testUserAgents = {
  chrome: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  firefox: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
  safari: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
  brave: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/1.60.125',
  arc: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Arc/1.0.0',
  comet: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Comet/1.0.0',
  edge: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
  opera: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0'
};

// Mock navigator.userAgent for testing
export const mockUserAgent = (userAgent: string) => {
  Object.defineProperty(navigator, 'userAgent', {
    value: userAgent,
    configurable: true
  });
};

// Test browser detection with different user agents
export const testBrowserDetection = (): BrowserTestResult[] => {
  const results: BrowserTestResult[] = [];
  const supportedBrowsers = getSupportedBrowsers();
  
  // Test supported browsers
  Object.entries(testUserAgents).forEach(([browserKey, userAgent]) => {
    // Temporarily mock the user agent
    const originalUserAgent = navigator.userAgent;
    mockUserAgent(userAgent);
    
    try {
      const detected = detectBrowser();
      const expectedName = browserKey === 'arc' ? 'Arc Browser' : 
                          browserKey.charAt(0).toUpperCase() + browserKey.slice(1);
      
      const isSupported = supportedBrowsers.includes(expectedName);
      const isDetectedCorrectly = detected.name === expectedName;
      
      results.push({
        browserName: expectedName,
        isSupported,
        isDetectedCorrectly,
        expectedBrowsers: supportedBrowsers,
        testPassed: isSupported === detected.isSupported && 
                   (isSupported ? isDetectedCorrectly : true)
      });
    } finally {
      // Restore original user agent
      mockUserAgent(originalUserAgent);
    }
  });
  
  return results;
};

// Verify current browser support
export const verifyCurrentBrowser = (): {
  isSupported: boolean;
  browserName: string;
  supportedBrowsers: string[];
  recommendation: string;
} => {
  const browser = detectBrowser();
  const supportedBrowsers = getSupportedBrowsers();
  
  return {
    isSupported: browser.isSupported,
    browserName: browser.name,
    supportedBrowsers,
    recommendation: browser.isSupported 
      ? `✅ ${browser.name} is fully supported!`
      : `❌ ${browser.name} is not supported. Please use: ${supportedBrowsers.join(', ')}`
  };
};

// Check if all required browsers are supported
export const validateBrowserSupport = (): {
  allSupported: boolean;
  supportedCount: number;
  requiredBrowsers: string[];
  missingSupportFor: string[];
} => {
  const requiredBrowsers = ['Comet', 'Chrome', 'Arc Browser', 'Safari', 'Firefox', 'Brave'];
  const supportedBrowsers = getSupportedBrowsers();
  
  const missingSupportFor = requiredBrowsers.filter(
    browser => !supportedBrowsers.includes(browser)
  );
  
  return {
    allSupported: missingSupportFor.length === 0,
    supportedCount: supportedBrowsers.length,
    requiredBrowsers,
    missingSupportFor
  };
};

// Get browser feature compatibility
export const getBrowserFeatureSupport = () => {
  const browser = detectBrowser();
  
  return {
    browserName: browser.name,
    speechRecognition: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
    vibration: 'vibrate' in navigator,
    geolocation: 'geolocation' in navigator,
    notifications: 'Notification' in window,
    serviceWorker: 'serviceWorker' in navigator,
    webGL: !!document.createElement('canvas').getContext('webgl'),
    localStorage: 'localStorage' in window,
    sessionStorage: 'sessionStorage' in window,
    indexedDB: 'indexedDB' in window,
    webRTC: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
    fullscreen: !!(document.fullscreenEnabled || 'webkitFullscreenEnabled' in document),
    touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0
  };
};