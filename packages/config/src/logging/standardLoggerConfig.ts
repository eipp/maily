/**
 * Standardized logger configuration for all services
 * 
 * This module provides a consistent logging configuration across all services.
 */

import { createLogger, format, transports, Logger } from 'winston';

/**
 * Service environment
 */
export enum Environment {
  Development = 'development',
  Staging = 'staging',
  Production = 'production',
  Test = 'test',
}

/**
 * Logger configuration options
 */
export interface LoggerConfig {
  /**
   * Service name
   */
  serviceName: string;
  
  /**
   * Service version
   */
  serviceVersion?: string;
  
  /**
   * Environment
   */
  environment?: Environment;
  
  /**
   * Minimum log level
   */
  logLevel?: string;
  
  /**
   * Whether to output logs as JSON
   */
  jsonOutput?: boolean;
  
  /**
   * Whether to colorize console output
   */
  colorize?: boolean;
  
  /**
   * Additional transports
   */
  additionalTransports?: any[];
  
  /**
   * Custom fields to include in all log entries
   */
  defaultMeta?: Record<string, any>;
}

/**
 * Create a standardized logger
 * 
 * @param config Logger configuration
 * @returns Winston logger instance
 */
export function createStandardLogger(config: LoggerConfig): Logger {
  const {
    serviceName,
    serviceVersion = '1.0.0',
    environment = (process.env.NODE_ENV as Environment) || Environment.Development,
    logLevel = process.env.LOG_LEVEL || 'info',
    jsonOutput = environment !== Environment.Development,
    colorize = environment === Environment.Development,
    additionalTransports = [],
    defaultMeta = {},
  } = config;
  
  // Base metadata to include in all log entries
  const baseMetadata = {
    service: serviceName,
    version: serviceVersion,
    environment,
    ...defaultMeta,
  };
  
  // Create formatter based on environment
  const logFormat = jsonOutput
    ? format.combine(
        format.timestamp(),
        format.json(),
      )
    : format.combine(
        format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        colorize ? format.colorize() : format.uncolorize(),
        format.printf(({ timestamp, level, message, ...meta }) => {
          const metaString = Object.keys(meta).length > 0
            ? ` ${JSON.stringify(meta)}`
            : '';
            
          return `${timestamp} [${level}] [${serviceName}] ${message}${metaString}`;
        }),
      );
  
  // Create logger
  const logger = createLogger({
    level: logLevel,
    format: logFormat,
    defaultMeta: baseMetadata,
    transports: [
      new transports.Console(),
      ...additionalTransports,
    ],
  });
  
  // Add error handler
  logger.on('error', (error) => {
    console.error('Logger error:', error);
  });
  
  return logger;
}

/**
 * Request logging middleware factory for Express
 * 
 * @param logger Winston logger instance
 * @returns Express middleware
 */
export function createRequestLogger(logger: Logger) {
  return (req: any, res: any, next: any) => {
    const requestId = req.headers['x-request-id'] || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const start = Date.now();
    
    // Add request ID to request object
    req.requestId = requestId;
    
    // Add request ID to response headers
    res.setHeader('X-Request-ID', requestId);
    
    // Handle response finish
    res.on('finish', () => {
      const duration = Date.now() - start;
      
      logger.info(`${req.method} ${req.originalUrl || req.url} ${res.statusCode} ${duration}ms`, {
        method: req.method,
        url: req.originalUrl || req.url,
        status: res.statusCode,
        duration,
        requestId,
        userAgent: req.headers['user-agent'],
        ip: req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress,
      });
    });
    
    next();
  };
}

export default { createStandardLogger, createRequestLogger, Environment };