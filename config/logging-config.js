/**
 * Structured logging configuration for Node.js services
 */

const winston = require('winston');
const { format } = winston;

// Create custom log formatter with consistent fields
const structuredFormat = format.combine(
  format.timestamp(),
  format.errors({ stack: true }),
  format.metadata({ fillExcept: ['message', 'level', 'timestamp', 'stack'] }),
  format.json()
);

/**
 * Create a logger instance with standardized configuration
 * @param {Object} options - Logger configuration options
 * @param {string} options.serviceName - The name of the service
 * @param {string} options.environment - The current environment (production, staging, development)
 * @param {string} options.logLevel - The log level (debug, info, warn, error)
 * @returns {winston.Logger} Configured logger instance
 */
function createLogger({ serviceName, environment, logLevel = 'info' }) {
  // Validate required parameters
  if (!serviceName) {
    throw new Error('serviceName is required');
  }
  
  if (!environment) {
    throw new Error('environment is required');
  }
  
  // Create the logger
  const logger = winston.createLogger({
    level: logLevel,
    format: structuredFormat,
    defaultMeta: { 
      service: serviceName, 
      environment,
    },
    transports: [
      // Write to the console
      new winston.transports.Console(),
      
      // Production file logging
      ...(environment === 'production' ? [
        // Error log file
        new winston.transports.File({ 
          filename: `/var/log/maily/${serviceName}-error.log`, 
          level: 'error'
        }),
        // Combined log file
        new winston.transports.File({ 
          filename: `/var/log/maily/${serviceName}-combined.log` 
        }),
      ] : [])
    ],
  });
  
  // Add request context middleware for Express apps
  logger.requestMiddleware = function() {
    return (req, res, next) => {
      // Generate a trace ID for request tracking
      const traceId = req.headers['x-trace-id'] || generateTraceId();
      
      // Attach trace ID to response headers
      res.setHeader('x-trace-id', traceId);
      
      // Create a request-scoped logger with trace context
      req.logger = logger.child({
        traceId,
        requestId: req.id || traceId,
        userId: req.user?.id || 'anonymous',
        ip: req.ip || req.connection.remoteAddress,
        method: req.method,
        url: req.originalUrl || req.url,
      });
      
      // Log incoming requests
      req.logger.info('Request received');
      
      // Log when the response is completed
      res.on('finish', () => {
        req.logger.info('Response sent', {
          statusCode: res.statusCode,
          responseTime: Date.now() - req._startTime,
        });
      });
      
      next();
    };
  };
  
  return logger;
}

/**
 * Generate a random trace ID
 * @returns {string} Random trace ID
 */
function generateTraceId() {
  return `maily-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
}

/**
 * Add a correlation ID to the logger context for tracking related logs
 * @param {winston.Logger} logger - The logger instance
 * @param {string} correlationId - The correlation ID
 * @returns {winston.Logger} Logger with correlation context
 */
function withCorrelation(logger, correlationId) {
  return logger.child({ correlationId });
}

/**
 * Configure service-level logger with default settings
 * @param {string} serviceName - The name of the service
 * @returns {winston.Logger} Configured logger instance
 */
function configureServiceLogger(serviceName) {
  return createLogger({
    serviceName,
    environment: process.env.NODE_ENV || 'development',
    logLevel: process.env.LOG_LEVEL || 'info'
  });
}

module.exports = {
  createLogger,
  withCorrelation,
  configureServiceLogger,
};
