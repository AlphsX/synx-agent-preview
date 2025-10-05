'use client';

import { useEffect } from 'react';
import { generateFaviconSvg } from '@/utils/generateFavicon';

export function useDynamicFavicon(isDarkMode: boolean) {
  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;

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
    
    // Only update if the href is different to avoid unnecessary updates
    if (faviconLink.href !== faviconDataUri) {
      faviconLink.href = faviconDataUri;
    }

    // OLD PNG-based implementation (commented out for reference)
    // const faviconPath = isDarkMode ? '/icon-dark.png' : '/icon-light.png';
    // const currentHref = faviconLink.href;
    // const newHref = window.location.origin + faviconPath;
    // if (currentHref !== newHref) {
    //   faviconLink.href = faviconPath;
    // }
  }, [isDarkMode]);
}