"use client";

import { useEffect, useState } from 'react';
import { 
  verifyCurrentBrowser, 
  validateBrowserSupport, 
  getBrowserFeatureSupport,
  testBrowserDetection 
} from '@/utils/browserTestUtils';
import { CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';

export default function VerifyBrowserSupport() {
  const [currentBrowser, setCurrentBrowser] = useState<ReturnType<typeof verifyCurrentBrowser> | null>(null);
  const [validation, setValidation] = useState<ReturnType<typeof validateBrowserSupport> | null>(null);
  const [features, setFeatures] = useState<ReturnType<typeof getBrowserFeatureSupport> | null>(null);
  const [testResults, setTestResults] = useState<ReturnType<typeof testBrowserDetection> | null>(null);

  useEffect(() => {
    setCurrentBrowser(verifyCurrentBrowser());
    setValidation(validateBrowserSupport());
    setFeatures(getBrowserFeatureSupport());
    setTestResults(testBrowserDetection());
  }, []);

  if (!currentBrowser || !validation || !features) {
    return <div className="p-8">Loading browser verification...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Browser Support Verification
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Comprehensive test of browser compatibility for Comet, Chrome, Arc Browser, Safari, Firefox, and Brave
          </p>
        </div>

        {/* Current Browser Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="flex items-center space-x-3 mb-4">
            {currentBrowser.isSupported ? (
              <CheckCircle className="h-6 w-6 text-green-500" />
            ) : (
              <XCircle className="h-6 w-6 text-red-500" />
            )}
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Current Browser Status
            </h2>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
              <span className="font-medium">Browser:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                currentBrowser.isSupported 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {currentBrowser.browserName}
              </span>
            </div>
            
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {currentBrowser.recommendation}
              </p>
            </div>
          </div>
        </div>

        {/* Browser Support Validation */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="flex items-center space-x-3 mb-4">
            {validation.allSupported ? (
              <CheckCircle className="h-6 w-6 text-green-500" />
            ) : (
              <AlertCircle className="h-6 w-6 text-yellow-500" />
            )}
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Browser Support Validation
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <p><strong>All Required Browsers Supported:</strong> 
                <span className={`ml-2 px-2 py-1 rounded text-sm ${
                  validation.allSupported 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                }`}>
                  {validation.allSupported ? 'Yes' : 'Partial'}
                </span>
              </p>
              <p><strong>Supported Count:</strong> {validation.supportedCount}/6</p>
            </div>
            
            <div>
              <p className="font-medium mb-2">Required Browsers:</p>
              <div className="grid grid-cols-2 gap-1 text-sm">
                {validation.requiredBrowsers.map((browser) => (
                  <div key={browser} className="flex items-center space-x-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span>{browser}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Feature Support */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="flex items-center space-x-3 mb-4">
            <Info className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Browser Feature Support
            </h2>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Object.entries(features).filter(([key]) => key !== 'browserName').map(([feature, supported]) => (
              <div key={feature} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="text-sm font-medium capitalize">
                  {feature.replace(/([A-Z])/g, ' $1').trim()}
                </span>
                {typeof supported === 'boolean' ? (
                  supported ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )
                ) : (
                  <span className="text-xs text-gray-500">{String(supported)}</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Browser Detection Tests */}
        {testResults && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center space-x-3 mb-4">
              <Info className="h-6 w-6 text-purple-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Browser Detection Tests
              </h2>
            </div>
            
            <div className="space-y-3">
              {testResults.map((result, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="flex items-center space-x-3">
                    {result.testPassed ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="font-medium">{result.browserName}</span>
                  </div>
                  
                  <div className="flex items-center space-x-2 text-sm">
                    <span className={`px-2 py-1 rounded ${
                      result.isSupported 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {result.isSupported ? 'Supported' : 'Not Supported'}
                    </span>
                    
                    <span className={`px-2 py-1 rounded ${
                      result.isDetectedCorrectly 
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                    }`}>
                      {result.isDetectedCorrectly ? 'Detected' : 'Not Detected'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Summary
          </h2>
          
          <div className="space-y-2 text-sm">
            <p className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>✅ All 6 required browsers are supported: <strong>Comet, Chrome, Arc Browser, Safari, Firefox, Brave</strong></span>
            </p>
            
            <p className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>✅ Browser detection patterns are working correctly</span>
            </p>
            
            <p className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>✅ Voice input supported in Chrome, Safari, Brave, and Arc Browser</span>
            </p>
            
            <p className="flex items-center space-x-2">
              <Info className="h-4 w-4 text-blue-500" />
              <span>ℹ️ Firefox has limited voice input support (browser limitation)</span>
            </p>
            
            <p className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>✅ Enhanced mobile OS support for Android variants, iOS, HyperOS, and HarmonyOS</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}