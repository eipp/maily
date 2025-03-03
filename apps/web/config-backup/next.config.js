/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['justmaily.com', 'app.justmaily.com', 'cdn.justmaily.com'],
    formats: ['image/avif', 'image/webp'],
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  async rewrites() {
    return {
      beforeFiles: [
        // Handle API routes
        {
          source: '/api/:path*',
          destination: `${process.env.API_URL || 'https://api.justmaily.com'}/api/:path*`,
        },
      ],
    };
  },
  // Environment variables that will be available at build time
  env: {
    NEXT_PUBLIC_APP_URL: 'https://app.justmaily.com',
    NEXT_PUBLIC_LANDING_URL: 'https://justmaily.com',
    NEXT_PUBLIC_API_URL: 'https://api.justmaily.com',
    NEXT_PUBLIC_ANALYTICS_URL: 'https://analytics.justmaily.com',
  },
  // For optimizing third-party scripts
  experimental: {
    optimizeCss: true,
    scrollRestoration: true,
  },
};

module.exports = nextConfig;
