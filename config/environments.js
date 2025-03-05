/**
 * Maily Multi-Environment Configuration
 * 
 * This file defines all environment-specific configurations and provides
 * helper functions to load the correct configuration based on the current environment.
 */

const path = require('path');
const fs = require('fs');

// Define available environments
const ENVIRONMENTS = {
  PRODUCTION: 'production',
  STAGING: 'staging',
  TESTING: 'testing',
  DEVELOPMENT: 'development',
};

// Default environment
const DEFAULT_ENVIRONMENT = ENVIRONMENTS.DEVELOPMENT;

// Get current environment from NODE_ENV or default to development
const getCurrentEnvironment = () => {
  const env = process.env.NODE_ENV || DEFAULT_ENVIRONMENT;
  
  // Validate environment
  if (!Object.values(ENVIRONMENTS).includes(env)) {
    console.warn(`Warning: Unknown environment "${env}". Using "${DEFAULT_ENVIRONMENT}" instead.`);
    return DEFAULT_ENVIRONMENT;
  }
  
  return env;
};

// Environment-specific domain patterns
const DOMAIN_PATTERNS = {
  [ENVIRONMENTS.PRODUCTION]: {
    base: 'justmaily.com',
    web: 'app.justmaily.com',
    api: 'api.justmaily.com',
    analytics: 'analytics.justmaily.com',
    cdn: 'cdn.justmaily.com',
  },
  [ENVIRONMENTS.STAGING]: {
    base: 'staging.justmaily.com',
    web: 'staging-app.justmaily.com',
    api: 'staging-api.justmaily.com',
    analytics: 'staging-analytics.justmaily.com',
    cdn: 'staging-cdn.justmaily.com',
  },
  [ENVIRONMENTS.TESTING]: {
    base: 'test.justmaily.com',
    web: 'test-app.justmaily.com',
    api: 'test-api.justmaily.com',
    analytics: 'test-analytics.justmaily.com',
    cdn: 'test-cdn.justmaily.com',
  },
  [ENVIRONMENTS.DEVELOPMENT]: {
    base: 'dev.justmaily.com',
    web: 'dev-app.justmaily.com',
    api: 'dev-api.justmaily.com',
    analytics: 'dev-analytics.justmaily.com',
    cdn: 'dev-cdn.justmaily.com',
  },
};

// Environment-specific resource allocation
const RESOURCE_ALLOCATION = {
  [ENVIRONMENTS.PRODUCTION]: {
    cpu: {
      api: '1',
      web: '1',
      aiService: '2',
      emailService: '1',
      workers: '1',
    },
    memory: {
      api: '2G',
      web: '2G',
      aiService: '4G',
      emailService: '2G',
      workers: '2G',
    },
    replicas: {
      api: 3,
      web: 3,
      aiService: 2,
      emailService: 2, 
      workers: 3,
    },
  },
  [ENVIRONMENTS.STAGING]: {
    cpu: {
      api: '0.8',
      web: '0.8',
      aiService: '1.5',
      emailService: '0.8',
      workers: '0.8',
    },
    memory: {
      api: '1.5G',
      web: '1.5G',
      aiService: '3G',
      emailService: '1.5G',
      workers: '1.5G',
    },
    replicas: {
      api: 2,
      web: 2,
      aiService: 1,
      emailService: 1,
      workers: 2,
    },
  },
  [ENVIRONMENTS.TESTING]: {
    cpu: {
      api: '0.5',
      web: '0.5',
      aiService: '1',
      emailService: '0.5',
      workers: '0.5',
    },
    memory: {
      api: '1G',
      web: '1G',
      aiService: '2G',
      emailService: '1G',
      workers: '1G',
    },
    replicas: {
      api: 1,
      web: 1,
      aiService: 1,
      emailService: 1,
      workers: 1,
    },
  },
  [ENVIRONMENTS.DEVELOPMENT]: {
    cpu: {
      api: '0.3',
      web: '0.3',
      aiService: '0.5',
      emailService: '0.3',
      workers: '0.3',
    },
    memory: {
      api: '512M',
      web: '512M',
      aiService: '1G',
      emailService: '512M',
      workers: '512M',
    },
    replicas: {
      api: 1,
      web: 1,
      aiService: 1,
      emailService: 1,
      workers: 1,
    },
  },
};

// Database configuration by environment
const DATABASE_CONFIG = {
  [ENVIRONMENTS.PRODUCTION]: {
    host: 'maily-prod.cluster-xyz.us-west-2.rds.amazonaws.com',
    port: 5432,
    user: 'maily',
    password: process.env.DB_PASSWORD_PROD,
    database: 'maily',
    ssl: true,
  },
  [ENVIRONMENTS.STAGING]: {
    host: 'maily-staging.cluster-xyz.us-west-2.rds.amazonaws.com',
    port: 5432,
    user: 'maily',
    password: process.env.DB_PASSWORD_STAGING,
    database: 'maily',
    ssl: true,
  },
  [ENVIRONMENTS.TESTING]: {
    host: 'maily-test.cluster-xyz.us-west-2.rds.amazonaws.com',
    port: 5432,
    user: 'maily',
    password: process.env.DB_PASSWORD_TEST,
    database: 'maily',
    ssl: true,
  },
  [ENVIRONMENTS.DEVELOPMENT]: {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432', 10),
    user: process.env.POSTGRES_USER || 'maily',
    password: process.env.POSTGRES_PASSWORD || 'maily',
    database: process.env.POSTGRES_DB || 'maily',
    ssl: false,
  },
};

// Redis configuration by environment
const REDIS_CONFIG = {
  [ENVIRONMENTS.PRODUCTION]: {
    host: process.env.REDIS_HOST_PROD,
    port: parseInt(process.env.REDIS_PORT_PROD || '6379', 10),
    password: process.env.REDIS_PASSWORD_PROD,
  },
  [ENVIRONMENTS.STAGING]: {
    host: process.env.REDIS_HOST_STAGING,
    port: parseInt(process.env.REDIS_PORT_STAGING || '6379', 10),
    password: process.env.REDIS_PASSWORD_STAGING,
  },
  [ENVIRONMENTS.TESTING]: {
    host: process.env.REDIS_HOST_TEST,
    port: parseInt(process.env.REDIS_PORT_TEST || '6379', 10),
    password: process.env.REDIS_PASSWORD_TEST,
  },
  [ENVIRONMENTS.DEVELOPMENT]: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
  },
};

// Get environment-specific configuration
const getConfig = (environment = getCurrentEnvironment()) => {
  return {
    environment,
    domains: DOMAIN_PATTERNS[environment],
    resources: RESOURCE_ALLOCATION[environment],
    database: DATABASE_CONFIG[environment],
    redis: REDIS_CONFIG[environment],
    isProduction: environment === ENVIRONMENTS.PRODUCTION,
    isStaging: environment === ENVIRONMENTS.STAGING,
    isTesting: environment === ENVIRONMENTS.TESTING,
    isDevelopment: environment === ENVIRONMENTS.DEVELOPMENT,
  };
};

// Load environment-specific file
const loadEnvFile = (filePath) => {
  try {
    if (fs.existsSync(filePath)) {
      return require(filePath);
    }
  } catch (error) {
    console.error(`Error loading environment file: ${filePath}`, error);
  }
  
  return {};
};

// Load environment-specific configuration file
const loadEnvConfig = (baseName, environment = getCurrentEnvironment()) => {
  // Try to load environment-specific config
  const envConfigPath = path.resolve(__dirname, 'environments', environment, `${baseName}.js`);
  
  // Load default config as fallback
  const defaultConfigPath = path.resolve(__dirname, `${baseName}.js`);
  
  const envConfig = loadEnvFile(envConfigPath);
  const defaultConfig = loadEnvFile(defaultConfigPath);
  
  // Merge configs, with environment-specific taking precedence
  return { ...defaultConfig, ...envConfig };
};

module.exports = {
  ENVIRONMENTS,
  getCurrentEnvironment,
  getConfig,
  loadEnvConfig,
  DOMAIN_PATTERNS,
  RESOURCE_ALLOCATION,
  DATABASE_CONFIG,
  REDIS_CONFIG,
}; 