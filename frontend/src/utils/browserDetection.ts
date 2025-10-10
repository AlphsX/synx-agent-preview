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

  // Browser detection patterns (order matters for accurate detection)
  const browsers: Record<string, {
    pattern: RegExp;
    name: string;
    supported: boolean;
    exclude?: RegExp;
  }> = {
    // Comet Browser (check first as it might be based on Chromium)
    comet: {
      pattern: /comet/i,
      name: 'Comet',
      supported: true
    },
    // Arc Browser (check before Chrome as it's Chromium-based)
    arc: {
      pattern: /arc/i,
      name: 'Arc Browser',
      supported: true
    },
    // Brave Browser (check before Chrome as it's Chromium-based)
    brave: {
      pattern: /brave/i,
      name: 'Brave',
      supported: true
    },
    // Firefox (check before Chrome to avoid false positives)
    firefox: {
      pattern: /firefox/i,
      name: 'Firefox',
      supported: true
    },
    // Chrome (check after other Chromium-based browsers)
    chrome: {
      pattern: /chrome/i,
      name: 'Chrome',
      supported: true,
      exclude: /edg|opr|brave|arc|comet|firefox/i // Exclude other browsers
    },
    // Safari (check last as it might appear in other browser user agents)
    safari: {
      pattern: /safari/i,
      name: 'Safari',
      supported: true,
      exclude: /chrome|chromium|edg|opr|brave|arc|comet|firefox/i // Exclude other browsers
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
    
    // Provide specific guidance for supported browsers and mobile OS
    const userAgent = navigator.userAgent;
    
    if (browserInfo.name === 'Firefox') {
      message = `Voice input is not yet supported in Firefox. Please use Chrome, Safari, Brave, or Arc Browser for voice features.`;
    } else if (browserInfo.name === 'Safari') {
      if (/iPhone|iPad|iPod/i.test(userAgent)) {
        message = `Voice input requires iOS 14.5+ and Safari 14.1+. Please update your device.`;
      } else {
        message = `Voice input requires Safari 14.1+ on macOS. Please update your browser.`;
      }
    } else if (/Android/i.test(userAgent)) {
      if (/MIUI|HyperOS/i.test(userAgent)) {
        message = `Voice input on Xiaomi devices works best with Chrome. Please use Chrome browser.`;
      } else if (/HarmonyOS|EMUI/i.test(userAgent)) {
        message = `Voice input on Huawei devices works best with Chrome. Please use Chrome browser.`;
      } else if (/Samsung|OneUI/i.test(userAgent)) {
        message = `Voice input on Samsung devices works best with Chrome or Samsung Internet. Please use Chrome browser.`;
      } else {
        message = `Voice input on Android requires Chrome 25+. Please use Chrome browser.`;
      }
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