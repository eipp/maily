import winston from 'winston';
import { config } from './config';

/**
 * Log levels
 */
export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  HTTP = 'http',
  DEBUG = 'debug',
}

/**
 * Create a Winston logger instance with structured logging
 */
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'performance-optimization' },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, service, ...rest }) => {
          const meta = Object.keys(rest).length
            ? `\n${JSON.stringify(rest, null, 2)}`
            : '';
          return `${timestamp} [${service}] ${level}: ${message}${meta}`;
        })
      ),
    }),
  ],
});

// Add file transport in production
if (process.env.NODE_ENV === 'production') {
  logger.add(
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 10485760, // 10MB
      maxFiles: 5,
    })
  );

  logger.add(
    new winston.transports.File({
      filename: 'logs/performance.log',
      maxsize: 10485760, // 10MB
      maxFiles: 5,
    })
  );
}

// Create a stream for Morgan HTTP logging
logger.stream = {
  write: (message: string) => {
    logger.http(message.trim());
  },
};

/**
 * Log execution time of a function
 * @param fn Function to measure
 * @param fnName Function name for logging
 * @returns Function result
 */
export function logExecutionTime<T>(fn: () => T, fnName: string): T {
  const start = Date.now();

  try {
    const result = fn();

    const duration = Date.now() - start;
    logger.debug(`Executed ${fnName}`, { duration });

    return result;
  } catch (error: any) {
    const duration = Date.now() - start;
    logger.error(`Error executing ${fnName}`, { duration, error: error.message });
    throw error;
  }
}

/**
 * Log execution time of an async function
 * @param fn Async function to measure
 * @param fnName Function name for logging
 * @returns Promise of function result
 */
export async function logAsyncExecutionTime<T>(fn: () => Promise<T>, fnName: string): Promise<T> {
  const start = Date.now();

  try {
    const result = await fn();

    const duration = Date.now() - start;
    logger.debug(`Executed ${fnName}`, { duration });

    return result;
  } catch (error: any) {
    const duration = Date.now() - start;
    logger.error(`Error executing ${fnName}`, { duration, error: error.message });
    throw error;
  }
}

export default logger;
