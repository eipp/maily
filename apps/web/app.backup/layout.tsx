import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from '@/lib/providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'JustMaily - Enterprise-Grade Email Marketing Platform',
  description: 'AI-powered email marketing platform with hybrid interface and enterprise-grade features',
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
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
