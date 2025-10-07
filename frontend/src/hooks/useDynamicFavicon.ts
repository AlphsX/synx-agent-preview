'use client';

import { useEffect, useRef } from 'react';
import { generateFaviconSvg } from '@/utils/generateFavicon';

export function useDynamicFavicon(isDarkMode: boolean) {
  const lastThemeRef = useRef<boolean | null>(null);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;

    // Skip if theme hasn't actually changed
    if (lastThemeRef.current === isDarkMode) return;
    lastThemeRef.current = isDarkMode;

    // Find existing favicon link element by id first, then by rel
    let faviconLink = document.getElementById('favicon') as HTMLLinkElement;
    
    if (!faviconLink) {
      faviconLink = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
    }
    
    // If no favicon link exists, create one
    if (!faviconLink) {
      faviconLink = document.createElement('link');
      faviconLink.rel = 'icon';
      faviconLink.type = 'image/svg+xml';
      faviconLink.id = 'favicon';
      document.head.appendChild(faviconLink);
    }

    // Generate SVG favicon based on theme
    const faviconDataUri = generateFaviconSvg(isDarkMode);
    
    // Update favicon type if needed
    if (faviconLink.type !== 'image/svg+xml') {
      faviconLink.type = 'image/svg+xml';
    }
    
    // Force update the favicon
    faviconLink.href = faviconDataUri;
  }, [isDarkMode]);
}