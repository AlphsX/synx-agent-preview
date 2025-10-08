'use client';

import { useState, useEffect } from 'react';

export function useAppLoading() {
  const [isLoading, setIsLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Simulate app initialization
    const initializeApp = async () => {
      // Wait for hydration
      setIsHydrated(true);
      
      // Minimum loading time for smooth UX
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Check if all critical resources are loaded
      if (document.readyState === 'complete') {
        setIsLoading(false);
      } else {
        window.addEventListener('load', () => {
          setTimeout(() => setIsLoading(false), 300);
        });
      }
    };

    initializeApp();
  }, []);

  return { isLoading, isHydrated };
}