/**
 * Logger utility for the Email Service
 * 
 * This module provides a structured logging utility for the Email Service,
 * with support for different log levels, structured metadata, and various
 * output formats.
 */

import winston from 'winston';
import { format } from 'winston';

// Environment variables
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const LOG_FORMAT = process.env.LOG_FORMAT || 'json';
const SERVICE_NAME = process.env.SERVICE_NAME || 'email-service';
const NODE_ENV = process.env.NODE_ENV || 'development';

// Create custom format for console output
const consoleFormat = format.printf(({ level, message, timestamp, ...metadata }) => {
  const metadataStr = Object.keys(metadata).length
    ? `\n${JSON.stringify(metadata, null, 2)}`
    : '';
  
  return `${timestamp} [${level.toUpperCase()}] ${message}${metadataStr}`;
});

// Create logger instance
export const logger = winston.createLogger({
  level: LOG_LEVEL,
  defaultMeta: {
    service: SERVICE_NAME,
    environment: NODE_ENV,
  },
  format: format.combine(
    format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
    format.errors({ stack: true }),
    LOG_FORMAT === 'json' ? format.json() : consoleFormat
  ),
  transports: [
    new winston.transports.Console({
      format: format.combine(
        format.colorize(),
        LOG_FORMAT === 'json' ? format.json() : consoleFormat
      ),
    }),
  ],
});

// Add file transport in production
if (NODE_ENV === 'production') {
  logger.add(
    new winston.transports.File({
      filename: 'logs/email-service-error.log',
      level: 'error',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 10,
    })
  );
  
  logger.add(
    new winston.transports.File({
      filename: 'logs/email-service-combined.log',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 10,
    })
  );
}

// Create child logger with request context
export function createRequestLogger(requestId: string, userId?: string) {
  return logger.child({
    requestId,
    userId,
  });
}

// Log HTTP requests
export function logHttpRequest(req: any, res: any, responseTime: number) {
  const { method, url, headers, ip } = req;
  const { statusCode } = res;
  
  logger.info('HTTP Request', {
    method,
    url,
    statusCode,
    responseTime,
    userAgent: headers['user-agent'],
    ip,
  });
}

// Log blockchain transactions
export function logBlockchainTransaction(
  transactionType: string,
  transactionHash: string,
  metadata: Record<string, any> = {}
) {
  logger.info(`Blockchain Transaction: ${transactionType}`, {
    transactionHash,
    ...metadata,
  });
}

// Log certificate operations
export function logCertificateOperation(
  operation: 'issue' | 'verify' | 'revoke',
  certificateId: string,
  metadata: Record<string, any> = {}
) {
  logger.info(`Certificate Operation: ${operation}`, {
    certificateId,
    ...metadata,
  });
}

// Log email operations
export function logEmailOperation(
  operation: 'send' | 'verify' | 'track',
  emailId: string,
  metadata: Record<string, any> = {}
) {
  logger.info(`Email Operation: ${operation}`, {
    emailId,
    ...metadata,
  });
}

// Log performance metrics
export function logPerformanceMetric(
  metricName: string,
  value: number,
  unit: string,
  metadata: Record<string, any> = {}
) {
  logger.info(`Performance Metric: ${metricName}`, {
    value,
    unit,
    ...metadata,
  });
}

// Log security events
export function logSecurityEvent(
  eventType: string,
  severity: 'low' | 'medium' | 'high' | 'critical',
  metadata: Record<string, any> = {}
) {
  const logMethod = severity === 'critical' || severity === 'high'
    ? logger.error
    : severity === 'medium'
      ? logger.warn
      : logger.info;
  
  logMethod(`Security Event: ${eventType}`, {
    severity,
    ...metadata,
  });
}

// Export default logger
export default logger;
