/** @type {import('next').NextConfig} */

const { withSentryConfig } = require('@sentry/nextjs');
const withBundleAnalyzer = process.env.ANALYZE === 'true'
  ? require('@next/bundle-analyzer')({ enabled: true })
  : (config) => config;

/**
 * Enhanced Next.js configuration with optimizations for production
 */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false, // Security: Remove X-Powered-By header
  generateEtags: true, // Performance: Generate ETags for caching
  compress: true, // Performance: Enable gzip compression
  productionBrowserSourceMaps: false, // Performance: Disable source maps in production

  // Asset optimization
  images: {
    domains: ['cdn.justmaily.com', 'storage.googleapis.com'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24, // 1 day
    formats: ['image/webp', 'image/avif'],
  },

  // Webpack optimization
  webpack: (config, { dev, isServer }) => {
    // Optimize CSS
    if (!dev && !isServer) {
      config.optimization.splitChunks.cacheGroups = {
        ...config.optimization.splitChunks.cacheGroups,
        // Extract CSS into a single chunk
        styles: {
          name: 'styles',
          test: /\.(css|scss)$/,
          chunks: 'all',
          enforce: true,
        },
        // Extract common dependencies into a separate chunk
        commons: {
          name: 'commons',
          chunks: 'all',
          minChunks: 2,
          priority: 10,
        },
        // Create a vendors chunk for node_modules
        vendors: {
          name: 'vendors',
          test: /[\\/]node_modules[\\/]/,
          chunks: 'all',
          priority: 20,
        },
        // Create separate chunks for large dependencies
        // This helps reduce the main bundle size
        react: {
          name: 'react',
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          chunks: 'all',
          priority: 30,
        },
        canvas: {
          name: 'canvas-lib',
          test: /[\\/]node_modules[\\/](tldraw|yjs|fabric)[\\/]/,
          chunks: 'all',
          priority: 25,
        },
        ai: {
          name: 'ai-lib',
          test: /[\\/]node_modules[\\/](@ai-sdk|openai|ai)[\\/]/,
          chunks: 'all',
          priority: 25,
        },
      };
    }

    // Tree shaking optimizations
    config.optimization.usedExports = true;

    // Add performance budgets
    if (!dev && !isServer) {
      config.performance = {
        hints: 'warning', // 'error' or false are also valid values
        maxEntrypointSize: 500000, // 500 KB
        maxAssetSize: 500000, // 500 KB
      };
    }

    // Optimize SVG files
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    return config;
  },

  // Enable experimental features for performance
  experimental: {
    optimizeCss: true, // CSS optimization
    scrollRestoration: true, // Restore scroll position

    // Prefetching optimization
    // Only prefetch visible links
    optimisticClientCache: true,

    // For better module reuse
    // Reduces duplication in the bundle
    esmExternals: 'loose',
  },

  // Content Security Policy
  headers: async () => [
    {
      // Apply to all routes
      source: '/:path*',
      headers: [
        // Security headers
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
          key: 'X-Content-Type-Options',
          value: 'nosniff',
        },
        {
          key: 'Referrer-Policy',
          value: 'strict-origin-when-cross-origin',
        },
        {
          key: 'X-Frame-Options',
          value: 'DENY',
        },
        {
          key: 'Permissions-Policy',
          value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
        },
        // Content Security Policy (CSP)
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com https://cdn.usefathom.com; connect-src 'self' https://api.justmaily.com https://cdn.usefathom.com https://api.openai.com; img-src 'self' https://cdn.justmaily.com https://storage.googleapis.com data: blob:; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' data:; frame-src 'self' https://js.stripe.com; object-src 'none'; base-uri 'self';",
        },
      ],
    },
    {
      // Don't apply CSP to API routes
      source: '/api/:path*',
      headers: [
        {
          key: 'Content-Security-Policy',
          value: '', // Remove CSP for API routes
        },
      ],
    },
  ],

  // Configure redirects for improved SEO and UX
  async redirects() {
    return [
      {
        source: '/signin',
        destination: '/login',
        permanent: true,
      },
      {
        source: '/register',
        destination: '/signup',
        permanent: true,
      },
    ];
  },

  // Enable React Server Components
  serverComponents: true,

  // Configure how assets are handled
  assetPrefix: process.env.NEXT_PUBLIC_CDN_URL || '',
};

// Add Sentry configuration in production
const sentryWebpackPluginOptions = {
  // Additional options for Sentry
  silent: process.env.NODE_ENV === 'development',
  // Disable uploading source maps in dev
  dryRun: process.env.NODE_ENV !== 'production',
};

// Apply configurations in order
module.exports = withBundleAnalyzer(
  withSentryConfig(nextConfig, sentryWebpackPluginOptions)
);
