import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'maily-frontend' },
  transports: [
    // Write all logs to console
    new winston.transports.Console({
      format: winston.format.combine(winston.format.colorize(), winston.format.simple()),
    }),
  ],
});

// Add file transport in production
if (process.env.NODE_ENV === 'production') {
  logger.add(
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    })
  );
  logger.add(
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    })
  );
}

// Custom log levels
export const LogLevel = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug',
} as const;

type LogLevel = (typeof LogLevel)[keyof typeof LogLevel];

interface LogContext {
  component?: string;
  userId?: string;
  requestId?: string;
  [key: string]: unknown;
}

class Logger {
  private static instance: Logger;
  private context: LogContext = {};

  private constructor() {}

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  setContext(context: Partial<LogContext>): void {
    this.context = { ...this.context, ...context };
  }

  clearContext(): void {
    this.context = {};
  }

  private formatMessage(message: string, context?: LogContext): object {
    return {
      message,
      timestamp: new Date().toISOString(),
      ...this.context,
      ...context,
    };
  }

  error(message: string, error?: Error, context?: LogContext): void {
    logger.error(this.formatMessage(message, context), { error });
  }

  warn(message: string, context?: LogContext): void {
    logger.warn(this.formatMessage(message, context));
  }

  info(message: string, context?: LogContext): void {
    logger.info(this.formatMessage(message, context));
  }

  debug(message: string, context?: LogContext): void {
    logger.debug(this.formatMessage(message, context));
  }

  // Performance logging
  logPerformance(operation: string, duration: number, context?: LogContext): void {
    this.info(`Performance: ${operation} took ${duration}ms`, {
      ...context,
      type: 'performance',
      duration,
      operation,
    });
  }

  // API request logging
  logApiRequest(
    method: string,
    url: string,
    status: number,
    duration: number,
    context?: LogContext
  ): void {
    this.info(`API ${method} ${url} - ${status}`, {
      ...context,
      type: 'api',
      method,
      url,
      status,
      duration,
    });
  }

  // Error boundary logging
  logErrorBoundary(error: Error, componentStack: string, context?: LogContext): void {
    this.error('React Error Boundary caught an error', error, {
      ...context,
      type: 'error_boundary',
      componentStack,
    });
  }
}

export const log = Logger.getInstance();

// Example usage:
// import { log } from '@/utils/logger';
//
// log.info('User logged in', { userId: '123', component: 'LoginForm' });
// log.error('API call failed', new Error('Network error'), { url: '/api/users' });
// log.logPerformance('image-processing', 150, { imageId: '456' });
