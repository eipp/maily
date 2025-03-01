const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

/**
 * This file extends the Next.js configuration to include the bundle analyzer.
 * To use it, run:
 * ANALYZE=true npm run build
 */

// Import the existing Next.js config
const nextConfig = require('./next.config.mjs');

// Export the config with bundle analyzer
module.exports = withBundleAnalyzer(nextConfig);
