"use client";

import { useEffect, useState } from 'react';
import { detectMobileOS, getMobilePatterns, checkMobileFeatures, getMobileRecommendations, type MobileInfo } from '@/utils/mobileDetection';

export default function TestMobileDetection() {
  const [mobileInfo, setMobileInfo] = useState<MobileInfo | null>(null);
  const [mobileFeatures, setMobileFeatures] = useState<ReturnType<typeof checkMobileFeatures> | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);

  useEffect(() => {
    const mobile = detectMobileOS();
    setMobileInfo(mobile);
    
    const features = checkMobileFeatures();
    setMobileFeatures(features);
    
    const recs = getMobileRecommendations(mobile);
    setRecommendations(recs);
  }, []);

  if (!mobileInfo || !mobileFeatures) {
    return <div className="p-8">Loading mobile detection...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">
          Enhanced Mobile Detection Test
        </h1>
        
        {/* Basic Mobile Info */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Device Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p><strong>Is Mobile:</strong> 
                <span className={`ml-2 px-2 py-1 rounded text-sm ${
                  mobileInfo.isMobile 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {mobileInfo.isMobile ? 'Yes' : 'No'}
                </span>
              </p>
              <p><strong>Is Tablet:</strong> 
                <span className={`ml-2 px-2 py-1 rounded text-sm ${
                  mobileInfo.isTablet 
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                }`}>
                  {mobileInfo.isTablet ? 'Yes' : 'No'}
                </span>
              </p>
              <p><strong>Operating System:</strong> 
                <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 rounded text-sm">
                  {mobileInfo.os}
                </span>
              </p>
              <p><strong>Brand:</strong> 
                <span className="ml-2 px-2 py-1 bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200 rounded text-sm">
                  {mobileInfo.brand}
                </span>
              </p>
            </div>
            <div>
              <p><strong>Model:</strong> {mobileInfo.model}</p>
              <p><strong>Has Touch:</strong> 
                <span className={`ml-2 px-2 py-1 rounded text-sm ${
                  mobileInfo.hasTouch 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {mobileInfo.hasTouch ? 'Yes' : 'No'}
                </span>
              </p>
              <p><strong>Orientation:</strong> 
                <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded text-sm">
                  {mobileInfo.orientation}
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Feature Support */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Feature Support
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { name: 'Vibration', supported: mobileFeatures.supportsVibration },
              { name: 'Speech Recognition', supported: mobileFeatures.supportsSpeechRecognition },
              { name: 'Geolocation', supported: mobileFeatures.supportsGeolocation },
              { name: 'Camera', supported: mobileFeatures.supportsCamera },
              { name: 'Notifications', supported: mobileFeatures.supportsNotifications },
              { name: 'Service Worker', supported: mobileFeatures.supportsServiceWorker },
              { name: 'WebGL', supported: mobileFeatures.supportsWebGL }
            ].map((feature) => (
              <div key={feature.name} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="font-medium">{feature.name}</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  feature.supported 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {feature.supported ? 'Yes' : 'No'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Screen Information */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Screen Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold mb-2">Screen Size</h3>
              <p>Width: {mobileFeatures.screenSize.width}px</p>
              <p>Height: {mobileFeatures.screenSize.height}px</p>
              <p>Available Width: {mobileFeatures.screenSize.availWidth}px</p>
              <p>Available Height: {mobileFeatures.screenSize.availHeight}px</p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Viewport Size</h3>
              <p>Width: {mobileFeatures.viewportSize.width}px</p>
              <p>Height: {mobileFeatures.viewportSize.height}px</p>
              <p>Device Pixel Ratio: {mobileFeatures.devicePixelRatio}</p>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
              Mobile Recommendations
            </h2>
            <ul className="space-y-2">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700 dark:text-gray-300">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* User Agent */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            User Agent
          </h2>
          <code className="text-xs bg-gray-100 dark:bg-gray-700 p-3 rounded block break-all">
            {mobileInfo.userAgent}
          </code>
        </div>

        {/* Pattern Matching */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Pattern Matching Results
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(getMobilePatterns()).map(([key, pattern]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="font-medium capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  pattern.test(navigator.userAgent) 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
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