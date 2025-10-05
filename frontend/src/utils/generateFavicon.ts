/**
 * Generate dynamic SVG favicon based on theme
 * Uses the LogoIcon SVG component converted to a data URI
 */

export function generateFaviconSvg(isDarkMode: boolean): string {
  // Color based on theme - matches system theme
  const color = isDarkMode ? '#ffffff' : '#000000';
  
  // SVG markup for the LogoIcon
  const svg = `
    <svg width="35" height="33" viewBox="0 0 35 33" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path 
        d="M13.2371 21.0407L24.3186 12.8506C24.8619 12.4491 25.6384 12.6057 25.8973 13.2294C27.2597 16.5185 26.651 20.4712 23.9403 23.1851C21.2297 25.8989 17.4581 26.4941 14.0108 25.1386L10.2449 26.8843C15.6463 30.5806 22.2053 29.6665 26.304 25.5601C29.5551 22.3051 30.562 17.8683 29.6205 13.8673L29.629 13.8758C28.2637 7.99809 29.9647 5.64871 33.449 0.844576C33.5314 0.730667 33.6139 0.616757 33.6964 0.5L29.1113 5.09055V5.07631L13.2343 21.0436" 
        fill="${color}"
      />
    </svg>
  `.trim();
  
  // Convert SVG to data URI
  const encoded = encodeURIComponent(svg)
    .replace(/'/g, '%27')
    .replace(/"/g, '%22');
  
  return `data:image/svg+xml,${encoded}`;
}
