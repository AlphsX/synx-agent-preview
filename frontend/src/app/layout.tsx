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
        {/* Mobile viewport configuration to prevent zoom and ensure proper scaling */}
        <meta 
          name="viewport" 
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"
        />
        {/* Default favicon - will be updated by useDynamicFavicon hook */}
        <link
          rel="icon"
          type="image/svg+xml"
          href="data:image/svg+xml,%3Csvg width='35' height='33' viewBox='0 0 35 33' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M13.2371 21.0407L24.3186 12.8506C24.8619 12.4491 25.6384 12.6057 25.8973 13.2294C27.2597 16.5185 26.651 20.4712 23.9403 23.1851C21.2297 25.8989 17.4581 26.4941 14.0108 25.1386L10.2449 26.8843C15.6463 30.5806 22.2053 29.6665 26.304 25.5601C29.5551 22.3051 30.562 17.8683 29.6205 13.8673L29.629 13.8758C28.2637 7.99809 29.9647 5.64871 33.449 0.844576C33.5314 0.730667 33.6139 0.616757 33.6964 0.5L29.1113 5.09055V5.07631L13.2343 21.0436' fill='%23000000'/%3E%3C/svg%3E"
          id="favicon"
        />

        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  var isMobile = window.innerWidth < 768;
                  
                  // If no theme is set, default to system preference
                  if (!theme || theme === 'null' || theme === 'undefined') {
                    localStorage.setItem('theme', 'system');
                    theme = 'system';
                  }
                  
                  var shouldBeDark = theme === 'dark' || (theme === 'system' && prefersDark);
                  
                  // Clear any existing dark class first
                  document.documentElement.classList.remove('dark');
                  
                  if (shouldBeDark) {
                    document.documentElement.classList.add('dark');
                  }
                  
                  // Debug log for mobile
                  if (isMobile) {
                    console.log('Layout Script:', {
                      theme: theme,
                      prefersDark: prefersDark,
                      shouldBeDark: shouldBeDark,
                      documentHasDark: document.documentElement.classList.contains('dark')
                    });
                  }
                } catch (e) {
                  console.error('Layout theme script error:', e);
                  // Fallback to system preference
                  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.documentElement.classList.add('dark');
                  }
                }
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${inter.variable} antialiased`}
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
