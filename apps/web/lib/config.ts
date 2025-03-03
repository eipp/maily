any/**
 * Application configuration
 */

// Environment variables with defaults
const env = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  NEXT_PUBLIC_WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000',
  NEXT_PUBLIC_AUTH0_DOMAIN: process.env.NEXT_PUBLIC_AUTH0_DOMAIN || 'maily.us.auth0.com',
  NEXT_PUBLIC_AUTH0_CLIENT_ID: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || '',
  NEXT_PUBLIC_AUTH0_AUDIENCE: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE || 'https://api.maily.com',
};

// Derived URLs
const appUrl = env.NEXT_PUBLIC_APP_URL;
const apiUrl = env.NEXT_PUBLIC_API_URL;
const websocketUrl = env.NEXT_PUBLIC_WEBSOCKET_URL;

// Feature flags
const featureFlags = {
  aiMesh: true,
  trustVerification: true,
  realTimeCollaboration: true,
  analytics: true,
  platformIntegrations: true,
};

// Application metadata
const meta = {
  name: 'JustMaily',
  description: 'Enterprise-Grade Hybrid Interface for Email Marketing with AI Mesh Network',
  version: '1.0.0',
  author: 'JustMaily Team',
  support: 'support@justmaily.com',
};

// URLs
const urls = {
  app: appUrl,
  api: apiUrl,
  websocket: websocketUrl,
  landing: 'https://justmaily.com',
  docs: 'https://docs.justmaily.com',
  support: 'https://support.justmaily.com',
  blog: 'https://blog.justmaily.com',
  github: 'https://github.com/justmaily/justmaily',
};

// Theme configuration
const theme = {
  colors: {
    primary: {
      light: '#3b82f6', // blue-500
      DEFAULT: '#2563eb', // blue-600
      dark: '#1d4ed8', // blue-700
    },
    secondary: {
      light: '#a855f7', // purple-500
      DEFAULT: '#9333ea', // purple-600
      dark: '#7e22ce', // purple-700
    },
    accent: {
      light: '#f97316', // orange-500
      DEFAULT: '#ea580c', // orange-600
      dark: '#c2410c', // orange-700
    },
    success: {
      light: '#22c55e', // green-500
      DEFAULT: '#16a34a', // green-600
      dark: '#15803d', // green-700
    },
    warning: {
      light: '#eab308', // yellow-500
      DEFAULT: '#ca8a04', // yellow-600
      dark: '#a16207', // yellow-700
    },
    error: {
      light: '#ef4444', // red-500
      DEFAULT: '#dc2626', // red-600
      dark: '#b91c1c', // red-700
    },
    info: {
      light: '#0ea5e9', // sky-500
      DEFAULT: '#0284c7', // sky-600
      dark: '#0369a1', // sky-700
    },
  },
  fonts: {
    sans: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },
  breakpoints: {
    xs: '480px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
};

// AI configuration
const ai = {
  models: {
    content: 'claude-3-sonnet-20240229',
    design: 'gemini-1.5-pro',
    analytics: 'gpt-4o',
    coordinator: 'claude-3-opus-20240229',
  },
  maxTokens: {
    content: 4096,
    design: 8192,
    analytics: 4096,
    coordinator: 8192,
  },
  temperature: {
    content: 0.7,
    design: 0.5,
    analytics: 0.3,
    coordinator: 0.2,
  },
};

// Export configuration
const config = {
  env,
  featureFlags,
  meta,
  urls,
  theme,
  ai,
  isDev: env.NODE_ENV === 'development',
  isProd: env.NODE_ENV === 'production',
  isTest: env.NODE_ENV === 'test',
};

export default config;
