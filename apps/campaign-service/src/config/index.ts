import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from .env file
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

/**
 * Environment variables with defaults
 */
const config = {
  /**
   * Environment name
   */
  env: process.env.NODE_ENV || 'development',

  /**
   * Is production environment
   */
  isProduction: process.env.NODE_ENV === 'production',

  /**
   * Is development environment
   */
  isDevelopment: process.env.NODE_ENV === 'development' || !process.env.NODE_ENV,

  /**
   * Is test environment
   */
  isTest: process.env.NODE_ENV === 'test',

  /**
   * Server configuration
   */
  server: {
    /**
     * Server port
     */
    port: parseInt(process.env.PORT || '5000', 10),

    /**
     * API prefix
     */
    apiPrefix: process.env.API_PREFIX || '/api',

    /**
     * CORS allowed origins
     */
    corsOrigins: process.env.CORS_ORIGINS
      ? process.env.CORS_ORIGINS.split(',')
      : ['http://localhost:3000'],
  },

  /**
   * Database configuration
   */
  database: {
    /**
     * Database URL
     */
    url: process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/campaign_service',

    /**
     * Database schema
     */
    schema: process.env.DATABASE_SCHEMA || 'public',

    /**
     * Database pool size
     */
    poolSize: parseInt(process.env.DATABASE_POOL_SIZE || '5', 10),
  },

  /**
   * Event store configuration
   */
  eventStore: {
    /**
     * Event store type
     */
    type: process.env.EVENT_STORE_TYPE || 'postgres',

    /**
     * Event store connection string
     */
    connectionString:
      process.env.EVENT_STORE_CONNECTION_STRING ||
      'postgres://postgres:postgres@localhost:5432/campaign_events',

    /**
     * Event store schema
     */
    schema: process.env.EVENT_STORE_SCHEMA || 'events',
  },

  /**
   * Redis configuration
   */
  redis: {
    /**
     * Redis host
     */
    host: process.env.REDIS_HOST || 'localhost',

    /**
     * Redis port
     */
    port: parseInt(process.env.REDIS_PORT || '6379', 10),

    /**
     * Redis password
     */
    password: process.env.REDIS_PASSWORD || '',

    /**
     * Redis default TTL in seconds
     */
    ttl: parseInt(process.env.REDIS_TTL || '3600', 10),
  },

  /**
   * RabbitMQ configuration
   */
  rabbitmq: {
    /**
     * RabbitMQ URL
     */
    url: process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672',

    /**
     * RabbitMQ exchange
     */
    exchange: process.env.RABBITMQ_EXCHANGE || 'maily-events',

    /**
     * RabbitMQ queue
     */
    queue: process.env.RABBITMQ_QUEUE || 'campaign-events',
  },

  /**
   * JWT configuration
   */
  jwt: {
    /**
     * JWT secret
     */
    secret: process.env.JWT_SECRET || 'your-secret-key-change-in-production',

    /**
     * JWT expiration time
     */
    expiresIn: process.env.JWT_EXPIRES_IN || '1d',
  },

  /**
   * Logging configuration
   */
  logging: {
    /**
     * Log level
     */
    level: process.env.LOG_LEVEL || 'info',

    /**
     * Log file path
     */
    filePath: process.env.LOG_FILE_PATH || 'logs/campaign-service.log',
  },

  /**
   * Metrics configuration
   */
  metrics: {
    /**
     * Whether metrics are enabled
     */
    enabled: process.env.METRICS_ENABLED === 'true',

    /**
     * Metrics port
     */
    port: parseInt(process.env.METRICS_PORT || '9090', 10),
  },
};

export default config;
