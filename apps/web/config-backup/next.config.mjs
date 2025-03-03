import withPWA from 'next-pwa';
import withBundleAnalyzer from '@next/bundle-analyzer';
import CompressionPlugin from 'compression-webpack-plugin';

/**
 * @file Standardized Next.js configuration for Maily web application
 *
 * This configuration combines the best features from all previous configurations
 * and follows modern Next.js best practices with ES modules.
 */

const bundleAnalyzer = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Internationalization
  i18n: {
    locales: ['en', 'es', 'fr'],
    defaultLocale: 'en',
  },

  // Image optimization
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60,
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Asset optimization
  compress: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Static file serving configuration
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/image/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=60, stale-while-revalidate=30',
          },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store',
          },
        ],
      },
    ];
  },

  // Webpack configuration for optimization
  webpack: (config, { dev, isServer }) => {
    // Optimize CSS
    if (!dev && !isServer) {
      config.optimization.splitChunks.cacheGroups.styles = {
        name: 'styles',
        test: /\.(css|scss)$/,
        chunks: 'all',
        enforce: true,
      };

      // Enable Brotli and Gzip compression in production
      config.plugins.push(
        new CompressionPlugin({
          filename: '[path][base].br',
          algorithm: 'brotliCompress',
          test: /\.(js|css|html|svg)$/,
          compressionOptions: {
            level: 11,
          },
          threshold: 10240,
          minRatio: 0.8,
          deleteOriginalAssets: false,
        }),
        new CompressionPlugin({
          filename: '[path][base].gz',
          algorithm: 'gzip',
          test: /\.(js|css|html|svg)$/,
          threshold: 10240,
          minRatio: 0.8,
          deleteOriginalAssets: false,
        })
      );
    }

    return config;
  },

  experimental: {
    serverActions: true,
    optimizeCss: true, // Enable CSS optimization
    optimizePackageImports: ['@emotion/react', '@emotion/styled'],
  },

  // Enable page optimization
  poweredByHeader: false,
  generateEtags: true,

  // Progressive Web App configuration
  pwa: {
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development',
    runtimeCaching: [
      {
        urlPattern: /^https?.*/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'offlineCache',
          networkTimeoutSeconds: 15,
          expiration: {
            maxEntries: 150,
            maxAgeSeconds: 30 * 24 * 60 * 60, // 1 month
          },
          cacheableResponse: {
            statuses: [0, 200],
          },
        },
      },
      {
        urlPattern: /\.(png|jpg|jpeg|svg|gif|webp)$/,
        handler: 'CacheFirst',
        options: {
          cacheName: 'imageCache',
          expiration: {
            maxEntries: 50,
            maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
          },
        },
      },
      {
        urlPattern: /\.(js|css)$/,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'staticCache',
        },
      },
    ],
  },
};

// Wrap the config with PWA
const withPWAConfig = withPWA({
  dest: 'public',
  register: true,
  skipWaiting: true,
})(nextConfig);

// Export the config with both PWA and Bundle Analyzer
export default bundleAnalyzer(withPWAConfig);
