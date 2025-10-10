"use client";

import { useEffect, useState } from 'react';
import { detectBrowser, getSupportedBrowsers, getBrowserRecommendation, checkSpeechRecognitionSupport, type BrowserInfo } from '@/utils/browserDetection';
import { BrowserCompatibilityWarning } from '@/components/ui/browser-compatibility-warning';

export default function TestBrowserDetection() {
  const [browserInfo, setBrowserInfo] = useState<BrowserInfo | null>(null);
  const [speechSupport, setSpeechSupport] = useState<{ supported: boolean; message: string } | null>(null);

  useEffect(() => {
    const browser = detectBrowser();
    setBrowserInfo(browser);
    
    const speech = checkSpeechRecognitionSupport(browser);
    setSpeechSupport(speech);
  }, []);

  if (!browserInfo) {
    return <div className="p-8">Loading browser detection...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <BrowserCompatibilityWarning showAlways={true} />
      
      <div className="max-w-4xl mx-auto space-y-6 mt-16">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          Browser Detection Test
        </h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Current Browser
          </h2>
          <div className="space-y-2">
            <p><strong>Name:</strong> {browserInfo.name}</p>
            <p><strong>Version:</strong> {browserInfo.version}</p>
            <p><strong>Supported:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-sm ${
                browserInfo.isSupported 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {browserInfo.isSupported ? 'Yes' : 'No'}
              </span>
            </p>
            <p><strong>User Agent:</strong> <code className="text-sm bg-gray-100 dark:bg-gray-700 p-1 rounded">{browserInfo.userAgent}</code></p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Speech Recognition Support
          </h2>
          {speechSupport && (
            <div className="space-y-2">
              <p><strong>Supported:</strong> 
                <span className={`ml-2 px-2 py-1 rounded text-sm ${
                  speechSupport.supported 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {speechSupport.supported ? 'Yes' : 'No'}
                </span>
              </p>
              <p><strong>Message:</strong> {speechSupport.message}</p>
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Browser Recommendation
          </h2>
          <p className="text-gray-700 dark:text-gray-300">
            {getBrowserRecommendation(browserInfo)}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Supported Browsers
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {getSupportedBrowsers().map((browser) => (
              <div 
                key={browser}
                className={`p-3 rounded-lg border-2 text-center ${
                  browserInfo.name === browser
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                    : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                <div className="font-medium">{browser}</div>
                {browserInfo.name === browser && (
                  <div className="text-xs mt-1">✓ Current Browser</div>
                )}
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
              Browser Support Status
            </h3>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              All 6 browsers are fully supported: <strong>Comet, Chrome, Arc Browser, Safari, Firefox, and Brave</strong>
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
              Voice input works in Chrome, Safari, Brave, and Arc Browser. Firefox support is limited.
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            API Availability
          </h2>
          <div className="space-y-2">
            <p><strong>SpeechRecognition:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-sm ${
                (window.SpeechRecognition || window.webkitSpeechRecognition)
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {(window.SpeechRecognition || window.webkitSpeechRecognition) ? 'Available' : 'Not Available'}
              </span>
            </p>
            <p><strong>Navigator.vibrate:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-sm ${
                'vibrate' in navigator
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {'vibrate' in navigator ? 'Available' : 'Not Available'}
              </span>
            </p>
            <p><strong>Touch Support:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-sm ${
                ('ontouchstart' in window || navigator.maxTouchPoints > 0)
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {('ontouchstart' in window || navigator.maxTouchPoints > 0) ? 'Available' : 'Not Available'}
              </span>
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Browser Detection Patterns
          </h2>
          <div className="space-y-2 text-sm">
            {[
              { name: 'Comet', pattern: /comet/i },
              { name: 'Arc Browser', pattern: /arc/i },
              { name: 'Brave', pattern: /brave/i },
              { name: 'Firefox', pattern: /firefox/i },
              { name: 'Chrome', pattern: /chrome/i },
              { name: 'Safari', pattern: /safari/i }
            ].map(({ name, pattern }) => (
              <div key={name} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="font-medium">{name}</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  pattern.test(navigator.userAgent)
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-200'
                }`}>
                  {pattern.test(navigator.userAgent) ? 'Match' : 'No Match'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}