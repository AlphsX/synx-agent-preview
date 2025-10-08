/**
 * Browser Detection Utility
 * Detects supported browsers: Comet, Chrome, Arc Browser, Safari, Firefox, Brave
 */

export interface BrowserInfo {
  name: string;
  version: string;
  isSupported: boolean;
  userAgent: string;
}

export const detectBrowser = (): BrowserInfo => {
  const userAgent = navigator.userAgent;
  const userAgentLower = userAgent.toLowerCase();

  // Browser detection patterns
  const browsers: Record<string, {
    pattern: RegExp;
    name: string;
    supported: boolean;
    exclude?: RegExp;
  }> = {
    // Comet Browser
    comet: {
      pattern: /comet/i,
      name: 'Comet',
      supported: true
    },
    // Arc Browser
    arc: {
      pattern: /arc/i,
      name: 'Arc Browser',
      supported: true
    },
    // Brave Browser (must be checked before Chrome)
    brave: {
      pattern: /brave/i,
      name: 'Brave',
      supported: true
    },
    // Chrome (must be checked after Brave and Arc)
    chrome: {
      pattern: /chrome/i,
      name: 'Chrome',
      supported: true,
      exclude: /edg|opr|brave|arc|comet/i // Exclude Edge, Opera, Brave, Arc, Comet
    },
    // Safari (must be checked after Chrome-based browsers)
    safari: {
      pattern: /safari/i,
      name: 'Safari',
      supported: true,
      exclude: /chrome|chromium|edg|opr|brave|arc|comet/i // Exclude Chrome-based browsers
    },
    // Firefox
    firefox: {
      pattern: /firefox/i,
      name: 'Firefox',
      supported: true
    }
  };

  // Check each browser in order of priority
  for (const [key, browser] of Object.entries(browsers)) {
    if (browser.pattern.test(userAgentLower)) {
      // Check if this browser should be excluded (for Chrome/Safari detection)
      if (browser.exclude && browser.exclude.test(userAgentLower)) {
        continue;
      }

      // Extract version
      let version = 'Unknown';
      try {
        if (key === 'chrome') {
          const match = userAgent.match(/Chrome\/(\d+\.\d+)/);
          version = match ? match[1] : 'Unknown';
        } else if (key === 'safari') {
          const match = userAgent.match(/Version\/(\d+\.\d+)/);
          version = match ? match[1] : 'Unknown';
        } else if (key === 'firefox') {
          const match = userAgent.match(/Firefox\/(\d+\.\d+)/);
          version = match ? match[1] : 'Unknown';
        } else if (key === 'brave') {
          // Brave doesn't expose version in user agent, use Chrome version
          const match = userAgent.match(/Chrome\/(\d+\.\d+)/);
          version = match ? match[1] : 'Unknown';
        } else if (key === 'arc') {
          // Arc uses Chrome engine, use Chrome version
          const match = userAgent.match(/Chrome\/(\d+\.\d+)/);
          version = match ? match[1] : 'Unknown';
        } else if (key === 'comet') {
          // Comet might use Chrome engine, try to extract version
          const match = userAgent.match(/Chrome\/(\d+\.\d+)/);
          version = match ? match[1] : 'Unknown';
        }
      } catch (error) {
        console.warn('Error extracting browser version:', error);
      }

      return {
        name: browser.name,
        version,
        isSupported: browser.supported,
        userAgent
      };
    }
  }

  // If no supported browser is detected
  return {
    name: 'Unknown',
    version: 'Unknown',
    isSupported: false,
    userAgent
  };
};

export const getSupportedBrowsers = (): string[] => {
  return ['Comet', 'Chrome', 'Arc Browser', 'Safari', 'Firefox', 'Brave'];
};

export const getBrowserRecommendation = (currentBrowser: BrowserInfo): string => {
  if (currentBrowser.isSupported) {
    return `You're using ${currentBrowser.name} ${currentBrowser.version} - fully supported!`;
  }

  const supportedBrowsers = getSupportedBrowsers();
  return `Your browser (${currentBrowser.name}) is not supported. Please use one of these browsers: ${supportedBrowsers.join(', ')}.`;
};

// Check if current browser supports speech recognition
export const checkSpeechRecognitionSupport = (browserInfo: BrowserInfo): {
  supported: boolean;
  message: string;
} => {
  if (!browserInfo.isSupported) {
    return {
      supported: false,
      message: `Voice input is not available in ${browserInfo.name}. Please use a supported browser: ${getSupportedBrowsers().join(', ')}.`
    };
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    let message = `Voice input is not supported in ${browserInfo.name}.`;
    
    // Provide specific guidance for supported browsers
    if (browserInfo.name === 'Firefox') {
      message = `Voice input is not yet supported in Firefox. Please use Chrome, Safari, Brave, or Arc Browser for voice features.`;
    } else if (browserInfo.name === 'Safari') {
      message = `Voice input requires Safari 14.1+ on macOS or iOS 14.5+. Please update your browser.`;
    }
    
    return {
      supported: false,
      message
    };
  }

  return {
    supported: true,
    message: `Voice input is available in ${browserInfo.name} ${browserInfo.version}.`
  };
};