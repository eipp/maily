import type { Metadata } from 'next';
import { Inter, Poppins } from 'next/font/google';
import { Providers } from '@/lib/providers';
import { ErrorBoundary } from 'packages/error-handling/src/react/ErrorBoundary';
import './globals.css';

// Font optimization with swap for fast first paint
const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const poppins = Poppins({
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-poppins',
});

export const metadata: Metadata = {
  title: {
    default: 'JustMaily - Enterprise-Grade Email Marketing Platform',
    template: '%s | JustMaily',
  },
  description: 'AI-powered email marketing platform with hybrid interface and enterprise-grade features',
  keywords: ['email marketing', 'AI email', 'marketing automation', 'personalization', 'analytics', 'enterprise email'],
  authors: [{ name: 'JustMaily Team' }],
  creator: 'JustMaily',
  metadataBase: new URL('https://justmaily.com'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://justmaily.com',
    siteName: 'JustMaily',
    title: 'JustMaily - Enterprise-Grade Email Marketing Platform',
    description: 'AI-powered email marketing platform with hybrid interface and enterprise-grade features',
    images: [
      {
        url: 'https://justmaily.com/og-image.png',
        width: 1200,
        height: 630,
        alt: 'JustMaily',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'JustMaily - Enterprise-Grade Email Marketing Platform',
    description: 'AI-powered email marketing platform with hybrid interface and enterprise-grade features',
    creator: '@justmaily',
    images: ['https://justmaily.com/twitter-image.png'],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${poppins.variable}`}>
      <head>
        {/* Preload critical assets for faster FCP */}
        <link
          rel="preload"
          href="/images/hero-illustration.webp"
          as="image"
          type="image/webp"
        />
        {/* Modern favicon set */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/site.webmanifest" />
        {/* Cache control for static assets */}
        <meta httpEquiv="Cache-Control" content="public, max-age=31536000, immutable" />
      </head>
      <body className={inter.className}>
        <ErrorBoundary 
          onError={(error, errorInfo) => {
            // Log to error monitoring service
            console.error('Root error boundary caught an error:', error, errorInfo);
          }}
          fallback={({ error, resetError }) => (
            <div className="error-container p-8 max-w-3xl mx-auto my-16 bg-white rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h2>
              <p className="mb-4 text-gray-700">
                We're sorry, but we encountered an unexpected error. Our team has been notified.
              </p>
              <div className="bg-gray-100 p-4 rounded mb-4">
                <p className="font-mono text-sm">{error.message}</p>
              </div>
              <button 
                onClick={resetError}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
              >
                Try Again
              </button>
            </div>
          )}
        >
          <Providers>
            <main>{children}</main>
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
