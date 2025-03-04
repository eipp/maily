/** @type {import('next').NextConfig} */
const path = require('path');
const fs = require('fs');

// Load internationalization configuration
const i18nConfigPath = path.join(process.cwd(), 'apps/web/i18n/config.js');
const { i18n } = fs.existsSync(i18nConfigPath) 
  ? require(i18nConfigPath)
  : { i18n: { locales: ['en'], defaultLocale: 'en' } };

// Bundle analyzer support
const withBundleAnalyzer = process.env.ANALYZE === 'true' 
  ? require('@next/bundle-analyzer')({ enabled: true })
  : (config) => config;

const securityHeaders = [
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https://*.justmaily.com https://api.justmaily.com; frame-ancestors 'none';",
  },
];

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    serverActions: true,
    optimizeCss: true,
    scrollRestoration: true,
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  images: {
    domains: ['justmaily.com', 'assets.justmaily.com'],
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    minimumCacheTTL: 31536000, // 1 year for static images
  },
  i18n,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
      // Static asset caching
      {
        source: '/:all*(svg|jpg|png|webp|avif|otf|ttf|woff|woff2)',
        locale: false,
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          }
        ],
      },
      {
        source: '/fonts/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          }
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          }
        ],
      },
    ];
  },
  webpack: (config, { isServer }) => {
    // Web3 polyfills
    if (!isServer) {
      config.resolve.fallback = {
        fs: false,
        net: false,
        tls: false,
        crypto: require.resolve('crypto-browserify'),
        stream: require.resolve('stream-browserify'),
        http: require.resolve('stream-http'),
        https: require.resolve('https-browserify'),
        os: require.resolve('os-browserify/browser'),
        zlib: require.resolve('browserify-zlib'),
      };
    }
    
    // Split chunks optimization for better caching
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        vendors: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10,
        },
        commons: {
          name: 'commons',
          chunks: 'all',
          minChunks: 2,
          priority: 5,
        },
        ui: {
          test: /[\\/]components[\\/]/,
          name: 'ui',
          chunks: 'all',
          priority: 15,
        },
      },
    };
    
    return config;
  },
  // Enable compression
  compress: true,
  // For performance monitoring
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
};

module.exports = withBundleAnalyzer(nextConfig);