import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: [], // Add domains for external images if needed
    formats: ['image/avif', 'image/webp'],
  },
  reactStrictMode: true,
  poweredByHeader: false, // Security: Remove X-Powered-By header
  compress: true, // Enable compression
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production', // Remove console.logs in production
  },
  typescript: {
    ignoreBuildErrors: false, // Enforce type checking
  },
};

export default nextConfig;
