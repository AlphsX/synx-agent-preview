"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, X, ExternalLink } from "lucide-react";
import {
  detectBrowser,
  getBrowserRecommendation,
  getSupportedBrowsers,
  type BrowserInfo,
} from "@/utils/browserDetection";

interface BrowserCompatibilityWarningProps {
  onDismiss?: () => void;
  showAlways?: boolean;
}

export const BrowserCompatibilityWarning = ({
  onDismiss,
  showAlways = false,
}: BrowserCompatibilityWarningProps) => {
  const [browserInfo, setBrowserInfo] = useState<BrowserInfo | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    const browser = detectBrowser();
    setBrowserInfo(browser);

    // Check if user has previously dismissed the warning
    const dismissed = localStorage.getItem("browser-warning-dismissed");
    setIsDismissed(dismissed === "true");

    // Show warning if browser is not supported and not dismissed
    if (!browser.isSupported && (!dismissed || showAlways)) {
      setIsVisible(true);
    }
  }, [showAlways]);

  const handleDismiss = () => {
    setIsVisible(false);
    setIsDismissed(true);
    localStorage.setItem("browser-warning-dismissed", "true");
    onDismiss?.();
  };

  const downloadLinks = {
    Chrome: "https://www.google.com/chrome/",
    Firefox: "https://www.mozilla.org/firefox/",
    Safari: "https://www.apple.com/safari/",
    Brave: "https://brave.com/",
    "Arc Browser": "https://arc.net/",
    Comet: "https://cometbrowser.com/", // Update with actual URL when available
  };

  if (!browserInfo || !isVisible) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium">
                Browser Compatibility Notice
              </p>
              <p className="text-xs opacity-90 mt-1">
                {getBrowserRecommendation(browserInfo)}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Download links for supported browsers */}
            <div className="hidden md:flex items-center space-x-2">
              <span className="text-xs opacity-75">Download:</span>
              {getSupportedBrowsers()
                .slice(0, 4)
                .map((browser) => (
                  <a
                    key={browser}
                    href={downloadLinks[browser as keyof typeof downloadLinks]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded transition-colors duration-200 flex items-center space-x-1"
                  >
                    <span>{browser}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ))}
            </div>

            <button
              onClick={handleDismiss}
              className="p-1 hover:bg-white/20 rounded transition-colors duration-200"
              aria-label="Dismiss browser warning"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Mobile download links */}
        <div className="md:hidden mt-3 pt-3 border-t border-white/20">
          <div className="grid grid-cols-2 gap-2">
            {getSupportedBrowsers().map((browser) => (
              <a
                key={browser}
                href={downloadLinks[browser as keyof typeof downloadLinks]}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs bg-white/20 hover:bg-white/30 px-3 py-2 rounded transition-colors duration-200 flex items-center justify-center space-x-1"
              >
                <span>{browser}</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Hook for browser compatibility checking
export const useBrowserCompatibility = () => {
  const [browserInfo, setBrowserInfo] = useState<BrowserInfo | null>(null);
  const [isSupported, setIsSupported] = useState(true);

  useEffect(() => {
    const browser = detectBrowser();
    setBrowserInfo(browser);
    setIsSupported(browser.isSupported);
  }, []);

  return {
    browserInfo,
    isSupported,
    supportedBrowsers: getSupportedBrowsers(),
    recommendation: browserInfo ? getBrowserRecommendation(browserInfo) : "",
  };
};
