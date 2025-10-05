import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "SynxAI",
  description: "Nothin' SpecialX~。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* SVG Favicon - dynamically colored based on theme */}
        <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg width='35' height='33' viewBox='0 0 35 33' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M13.2371 21.0407L24.3186 12.8506C24.8619 12.4491 25.6384 12.6057 25.8973 13.2294C27.2597 16.5185 26.651 20.4712 23.9403 23.1851C21.2297 25.8989 17.4581 26.4941 14.0108 25.1386L10.2449 26.8843C15.6463 30.5806 22.2053 29.6665 26.304 25.5601C29.5551 22.3051 30.562 17.8683 29.6205 13.8673L29.629 13.8758C28.2637 7.99809 29.9647 5.64871 33.449 0.844576C33.5314 0.730667 33.6139 0.616757 33.6964 0.5L29.1113 5.09055V5.07631L13.2343 21.0436' fill='%23000000'/%3E%3C/svg%3E" id="favicon" />
        
        {/* OLD PNG-based favicon (commented out for reference)
        <link rel="icon" type="image/png" href="/icon-light.png" id="favicon" />
        */}
        
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  var shouldBeDark = theme === 'dark' || (theme === 'system' && prefersDark) || (!theme && prefersDark);
                  
                  // Helper function to generate SVG favicon with dynamic color
                  function generateFaviconSvg(isDark) {
                    var color = isDark ? '%23ffffff' : '%23000000';
                    return "data:image/svg+xml,%3Csvg width='35' height='33' viewBox='0 0 35 33' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M13.2371 21.0407L24.3186 12.8506C24.8619 12.4491 25.6384 12.6057 25.8973 13.2294C27.2597 16.5185 26.651 20.4712 23.9403 23.1851C21.2297 25.8989 17.4581 26.4941 14.0108 25.1386L10.2449 26.8843C15.6463 30.5806 22.2053 29.6665 26.304 25.5601C29.5551 22.3051 30.562 17.8683 29.6205 13.8673L29.629 13.8758C28.2637 7.99809 29.9647 5.64871 33.449 0.844576C33.5314 0.730667 33.6139 0.616757 33.6964 0.5L29.1113 5.09055V5.07631L13.2343 21.0436' fill='" + color + "'/%3E%3C/svg%3E";
                  }
                  
                  if (shouldBeDark) {
                    document.documentElement.classList.add('dark');
                    // Set dark SVG favicon immediately
                    var favicon = document.getElementById('favicon');
                    if (favicon) {
                      favicon.type = 'image/svg+xml';
                      favicon.href = generateFaviconSvg(true);
                    }
                  } else {
                    document.documentElement.classList.remove('dark');
                    // Set light SVG favicon immediately
                    var favicon = document.getElementById('favicon');
                    if (favicon) {
                      favicon.type = 'image/svg+xml';
                      favicon.href = generateFaviconSvg(false);
                    }
                  }
                  
                  // OLD PNG-based implementation (commented out for reference)
                  // if (shouldBeDark) {
                  //   document.documentElement.classList.add('dark');
                  //   var favicon = document.getElementById('favicon');
                  //   if (favicon) favicon.href = '/icon-dark.png';
                  // } else {
                  //   document.documentElement.classList.remove('dark');
                  //   var favicon = document.getElementById('favicon');
                  //   if (favicon) favicon.href = '/icon-light.png';
                  // }
                } catch (e) {
                  // Fallback to light mode if there's any error
                  document.documentElement.classList.remove('dark');
                  var favicon = document.getElementById('favicon');
                  if (favicon) {
                    favicon.type = 'image/svg+xml';
                    favicon.href = "data:image/svg+xml,%3Csvg width='35' height='33' viewBox='0 0 35 33' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M13.2371 21.0407L24.3186 12.8506C24.8619 12.4491 25.6384 12.6057 25.8973 13.2294C27.2597 16.5185 26.651 20.4712 23.9403 23.1851C21.2297 25.8989 17.4581 26.4941 14.0108 25.1386L10.2449 26.8843C15.6463 30.5806 22.2053 29.6665 26.304 25.5601C29.5551 22.3051 30.562 17.8683 29.6205 13.8673L29.629 13.8758C28.2637 7.99809 29.9647 5.64871 33.449 0.844576C33.5314 0.730667 33.6139 0.616757 33.6964 0.5L29.1113 5.09055V5.07631L13.2343 21.0436' fill='%23000000'/%3E%3C/svg%3E";
                  }
                }
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.variable} antialiased`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}