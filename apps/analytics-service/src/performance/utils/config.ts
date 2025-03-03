import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from .env file
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

/**
 * Database types supported by query optimizer
 */
export enum DatabaseType {
  POSTGRES = 'postgres',
  MYSQL = 'mysql',
  MONGODB = 'mongodb',
  SQLSERVER = 'sqlserver',
}

/**
 * Cache storage types
 */
export enum CacheStorageType {
  MEMORY = 'memory',
  REDIS = 'redis',
}

/**
 * Application configuration
 */
export interface AppConfig {
  /**
   * Environment name
   */
  env: string;

  /**
   * Is production environment
   */
  isProduction: boolean;

  /**
   * Is development environment
   */
  isDevelopment: boolean;

  /**
   * Is test environment
   */
  isTest: boolean;

  /**
   * Server configuration
   */
  server: {
    /**
     * Server port
     */
    port: number;

    /**
     * API prefix
     */
    apiPrefix: string;

    /**
     * CORS allowed origins
     */
    corsOrigins: string[];
  };

  /**
   * Database configuration
   */
  database: {
    /**
     * Database type
     */
    type: DatabaseType;

    /**
     * Database URL
     */
    url: string;

    /**
     * Connection pool size
     */
    poolSize: number;

    /**
     * Statement timeout (ms)
     */
    statementTimeout: number;

    /**
     * Idle timeout (ms)
     */
    idleTimeout: number;

    /**
     * Enable query tracking
     */
    trackQueries: boolean;

    /**
     * Slow query threshold (ms)
     */
    slowQueryThreshold: number;
  };

  /**
   * Caching configuration
   */
  cache: {
    /**
     * Enable caching
     */
    enabled: boolean;

    /**
     * Cache storage type
     */
    storage: CacheStorageType;

    /**
     * Redis connection URL (if Redis storage)
     */
    redisUrl?: string;

    /**
     * Default TTL (seconds)
     */
    ttl: number;

    /**
     * Maximum cache size (items)
     */
    maxSize: number;
  };

  /**
   * Query optimization configuration
   */
  queryOptimizer: {
    /**
     * Enable query optimization
     */
    enabled: boolean;

    /**
     * Enable automatic indexing suggestions
     */
    suggestIndexes: boolean;

    /**
     * Minimum improvement threshold to apply optimization (%)
     */
    minImprovementThreshold: number;

    /**
     * Maximum query execution time (ms)
     */
    maxQueryExecutionTime: number;
  };

  /**
   * Monitoring configuration
   */
  monitoring: {
    /**
     * Enable performance monitoring
     */
    enabled: boolean;

    /**
     * Monitoring interval (ms)
     */
    interval: number;

    /**
     * Retention period (days)
     */
    retentionDays: number;

    /**
     * Enable Prometheus metrics
     */
    prometheusEnabled: boolean;

    /**
     * Prometheus metrics port
     */
    prometheusPort: number;
  };

  /**
   * Logging configuration
   */
  logging: {
    /**
     * Log level
     */
    level: string;

    /**
     * Log to file
     */
    logToFile: boolean;

    /**
     * Log file path
     */
    logFilePath: string;

    /**
     * Maximum log file size (bytes)
     */
    maxLogSize: number;

    /**
     * Maximum number of log files
     */
    maxLogFiles: number;
  };
}

/**
 * Default configuration values
 */
const defaultConfig: AppConfig = {
  env: process.env.NODE_ENV || 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isDevelopment: process.env.NODE_ENV === 'development' || !process.env.NODE_ENV,
  isTest: process.env.NODE_ENV === 'test',

  server: {
    port: parseInt(process.env.PORT || '3000', 10),
    apiPrefix: process.env.API_PREFIX || '/api',
    corsOrigins: process.env.CORS_ORIGINS
      ? process.env.CORS_ORIGINS.split(',')
      : ['http://localhost:3000'],
  },

  database: {
    type: (process.env.DB_TYPE as DatabaseType) || DatabaseType.POSTGRES,
    url: process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/postgres',
    poolSize: parseInt(process.env.DB_POOL_SIZE || '10', 10),
    statementTimeout: parseInt(process.env.DB_STATEMENT_TIMEOUT || '30000', 10),
    idleTimeout: parseInt(process.env.DB_IDLE_TIMEOUT || '10000', 10),
    trackQueries: process.env.TRACK_QUERIES === 'true',
    slowQueryThreshold: parseInt(process.env.SLOW_QUERY_THRESHOLD || '1000', 10),
  },

  cache: {
    enabled: process.env.CACHE_ENABLED !== 'false',
    storage: (process.env.CACHE_STORAGE as CacheStorageType) || CacheStorageType.MEMORY,
    redisUrl: process.env.REDIS_URL,
    ttl: parseInt(process.env.CACHE_TTL || '300', 10),
    maxSize: parseInt(process.env.CACHE_MAX_SIZE || '1000', 10),
  },

  queryOptimizer: {
    enabled: process.env.QUERY_OPTIMIZER_ENABLED !== 'false',
    suggestIndexes: process.env.SUGGEST_INDEXES !== 'false',
    minImprovementThreshold: parseInt(process.env.MIN_IMPROVEMENT_THRESHOLD || '10', 10),
    maxQueryExecutionTime: parseInt(process.env.MAX_QUERY_EXECUTION_TIME || '5000', 10),
  },

  monitoring: {
    enabled: process.env.MONITORING_ENABLED !== 'false',
    interval: parseInt(process.env.MONITORING_INTERVAL || '60000', 10),
    retentionDays: parseInt(process.env.MONITORING_RETENTION_DAYS || '7', 10),
    prometheusEnabled: process.env.PROMETHEUS_ENABLED === 'true',
    prometheusPort: parseInt(process.env.PROMETHEUS_PORT || '9090', 10),
  },

  logging: {
    level: process.env.LOG_LEVEL || 'info',
    logToFile: process.env.LOG_TO_FILE === 'true',
    logFilePath: process.env.LOG_FILE_PATH || 'logs/performance.log',
    maxLogSize: parseInt(process.env.MAX_LOG_SIZE || '10485760', 10), // 10MB
    maxLogFiles: parseInt(process.env.MAX_LOG_FILES || '5', 10),
  },
};

/**
 * Configuration object
 */
export const config: AppConfig = defaultConfig;

export default config;
