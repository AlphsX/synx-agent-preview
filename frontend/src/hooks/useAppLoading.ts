'use client';

import { useState, useEffect } from 'react';

export function useAppLoading() {
  const [isLoading, setIsLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Fast app initialization
    const initializeApp = async () => {
      // Mark as hydrated immediately
      setIsHydrated(true);
      
      // Reduced loading time for better UX (800ms instead of 1500ms)
      const minLoadTime = new Promise(resolve => setTimeout(resolve, 800));
      
      // Check if critical resources are loaded
      const resourcesLoaded = new Promise(resolve => {
        if (document.readyState === 'complete') {
          resolve(true);
        } else {
          window.addEventListener('load', () => resolve(true), { once: true });
        }
      });
      
      // Wait for both minimum time and resources
      await Promise.all([minLoadTime, resourcesLoaded]);
      
      // Small delay for smooth transition
      setTimeout(() => setIsLoading(false), 100);
    };

    initializeApp();
  }, []);

  return { isLoading, isHydrated };
}