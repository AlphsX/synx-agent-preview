/**
 * Enhanced Mobile Detection Utility
 * Supports: Android (Samsung, Google, OnePlus, OPPO), iOS (Apple), HyperOS (Xiaomi), HarmonyOS (Huawei), and more
 */

export interface MobileInfo {
  isMobile: boolean;
  isTablet: boolean;
  os: string;
  brand: string;
  model: string;
  userAgent: string;
  hasTouch: boolean;
  orientation: 'portrait' | 'landscape';
}

export const detectMobileOS = (): MobileInfo => {
  const userAgent = navigator.userAgent;

  // Basic mobile detection
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet/i.test(userAgent);
  const isMobileScreen = window.innerWidth <= 768;
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  const isMobile = isMobileUA || isMobileScreen || hasTouch;
  
  // Tablet detection
  const isTablet = /iPad|Android.*Tablet|Windows.*Touch/i.test(userAgent) || 
                   (isMobile && window.innerWidth >= 768);

  // OS Detection
  let os = 'Unknown';
  let brand = 'Unknown';
  let model = 'Unknown';

  // iOS Detection
  if (/iPhone|iPad|iPod/i.test(userAgent)) {
    os = 'iOS';
    brand = 'Apple';
    
    if (/iPhone/i.test(userAgent)) {
      model = 'iPhone';
    } else if (/iPad/i.test(userAgent)) {
      model = 'iPad';
    } else if (/iPod/i.test(userAgent)) {
      model = 'iPod';
    }
  }
  // Android and Custom OS Detection
  else if (/Android/i.test(userAgent)) {
    os = 'Android';
    
    // HyperOS (Xiaomi)
    if (/HyperOS|MIUI/i.test(userAgent)) {
      os = 'HyperOS';
      brand = 'Xiaomi';
      
      // Xiaomi device models
      if (/Mi\s+(\w+)/i.test(userAgent)) {
        const match = userAgent.match(/Mi\s+(\w+)/i);
        model = match ? `Mi ${match[1]}` : 'Xiaomi Device';
      } else if (/Redmi/i.test(userAgent)) {
        model = 'Redmi';
      }
    }
    // HarmonyOS (Huawei)
    else if (/HarmonyOS|EMUI/i.test(userAgent)) {
      os = 'HarmonyOS';
      brand = 'Huawei';
      
      if (/HUAWEI|Honor/i.test(userAgent)) {
        const huaweiMatch = userAgent.match(/HUAWEI\s+([^;)]+)/i);
        const honorMatch = userAgent.match(/Honor\s+([^;)]+)/i);
        model = huaweiMatch ? huaweiMatch[1] : honorMatch ? `Honor ${honorMatch[1]}` : 'Huawei Device';
      }
    }
    // Samsung (One UI)
    else if (/Samsung|SM-|Galaxy|OneUI/i.test(userAgent)) {
      brand = 'Samsung';
      
      if (/SM-([^;)]+)/i.test(userAgent)) {
        const match = userAgent.match(/SM-([^;)]+)/i);
        model = match ? `Galaxy ${match[1]}` : 'Samsung Galaxy';
      } else if (/Galaxy/i.test(userAgent)) {
        model = 'Samsung Galaxy';
      }
    }
    // OnePlus (OxygenOS)
    else if (/OnePlus|OxygenOS/i.test(userAgent)) {
      brand = 'OnePlus';
      
      if (/OnePlus\s+([^;)]+)/i.test(userAgent)) {
        const match = userAgent.match(/OnePlus\s+([^;)]+)/i);
        model = match ? match[1] : 'OnePlus Device';
      }
    }
    // OPPO (ColorOS)
    else if (/OPPO|ColorOS/i.test(userAgent)) {
      brand = 'OPPO';
      
      if (/OPPO\s+([^;)]+)/i.test(userAgent)) {
        const match = userAgent.match(/OPPO\s+([^;)]+)/i);
        model = match ? match[1] : 'OPPO Device';
      }
    }
    // Vivo (Funtouch OS)
    else if (/vivo|Funtouch/i.test(userAgent)) {
      brand = 'Vivo';
      
      if (/vivo\s+([^;)]+)/i.test(userAgent)) {
        const match = userAgent.match(/vivo\s+([^;)]+)/i);
        model = match ? match[1] : 'Vivo Device';
      }
    }
    // Google Pixel
    else if (/Pixel/i.test(userAgent)) {
      brand = 'Google';
      
      if (/Pixel\s+([^;)]+)/i.test(userAgent)) {
        const match = userAgent.match(/Pixel\s+([^;)]+)/i);
        model = match ? `Pixel ${match[1]}` : 'Google Pixel';
      }
    }
    // Generic Android
    else {
      brand = 'Android Device';
      model = 'Android';
    }
  }
  // Other mobile OS
  else if (/BlackBerry/i.test(userAgent)) {
    os = 'BlackBerry';
    brand = 'BlackBerry';
  }
  else if (/Windows Phone|IEMobile/i.test(userAgent)) {
    os = 'Windows Phone';
    brand = 'Microsoft';
  }
  else if (/webOS/i.test(userAgent)) {
    os = 'webOS';
    brand = 'LG';
  }

  // Orientation detection
  const orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';

  return {
    isMobile,
    isTablet,
    os,
    brand,
    model,
    userAgent,
    hasTouch,
    orientation
  };
};

// Enhanced mobile detection patterns for different use cases
export const getMobilePatterns = () => {
  return {
    // Basic mobile detection
    basic: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet/i,
    
    // Enhanced mobile detection with custom OS
    enhanced: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet|MIUI|HarmonyOS|HyperOS|EMUI|Funtouch|ColorOS|OxygenOS|OneUI/i,
    
    // Specific OS patterns
    ios: /iPhone|iPad|iPod/i,
    android: /Android/i,
    hyperOS: /HyperOS|MIUI/i,
    harmonyOS: /HarmonyOS|EMUI/i,
    
    // Brand patterns
    samsung: /Samsung|SM-|Galaxy|OneUI/i,
    xiaomi: /Xiaomi|Mi\s+|Redmi|MIUI|HyperOS/i,
    huawei: /HUAWEI|Honor|HarmonyOS|EMUI/i,
    oppo: /OPPO|ColorOS/i,
    vivo: /vivo|Funtouch/i,
    oneplus: /OnePlus|OxygenOS/i,
    google: /Pixel/i
  };
};

// Check if device supports specific features
export const checkMobileFeatures = () => {
  const mobileInfo = detectMobileOS();
  
  return {
    ...mobileInfo,
    supportsVibration: 'vibrate' in navigator,
    supportsSpeechRecognition: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
    supportsGeolocation: 'geolocation' in navigator,
    supportsCamera: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
    supportsNotifications: 'Notification' in window,
    supportsServiceWorker: 'serviceWorker' in navigator,
    supportsWebGL: !!document.createElement('canvas').getContext('webgl'),
    devicePixelRatio: window.devicePixelRatio || 1,
    screenSize: {
      width: window.screen.width,
      height: window.screen.height,
      availWidth: window.screen.availWidth,
      availHeight: window.screen.availHeight
    },
    viewportSize: {
      width: window.innerWidth,
      height: window.innerHeight
    }
  };
};

// Get mobile-specific recommendations
export const getMobileRecommendations = (mobileInfo: MobileInfo) => {
  const recommendations = [];
  
  if (mobileInfo.isMobile) {
    recommendations.push('Optimized for mobile experience');
    
    if (mobileInfo.os === 'iOS') {
      recommendations.push('Voice input works best in Safari on iOS');
      recommendations.push('Enable microphone access in Settings > Safari > Microphone');
    } else if (mobileInfo.os === 'Android' || mobileInfo.os.includes('Android')) {
      recommendations.push('Voice input works best in Chrome on Android');
      recommendations.push('Grant microphone permission when prompted');
    } else if (mobileInfo.os === 'HyperOS') {
      recommendations.push('MIUI/HyperOS detected - Voice input optimized for Xiaomi devices');
    } else if (mobileInfo.os === 'HarmonyOS') {
      recommendations.push('HarmonyOS detected - Voice input optimized for Huawei devices');
    }
    
    if (mobileInfo.brand === 'Samsung') {
      recommendations.push('Samsung device detected - One UI optimizations enabled');
    }
  }
  
  return recommendations;
};