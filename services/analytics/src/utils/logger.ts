/**
 * Logging utility for the analytics service
 */

import { createLogger as createWinstonLogger, format, transports } from 'winston';

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
 * Create a logger instance
 * @param serviceName Name of the service
 * @returns Configured logger
 */
export function createLogger(serviceName: string) {
  const logger = createWinstonLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: format.combine(
      format.timestamp(),
      format.errors({ stack: true }),
      format.json()
    ),
    defaultMeta: { service: serviceName },
    transports: [
      new transports.Console({
        format: format.combine(
          format.colorize(),
          format.printf(({ timestamp, level, message, service, ...rest }) => {
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
      new transports.File({
        filename: `logs/${serviceName}-error.log`,
        level: 'error',
        maxsize: 10485760, // 10MB
        maxFiles: 5,
      })
    );

    logger.add(
      new transports.File({
        filename: `logs/${serviceName}.log`,
        maxsize: 10485760, // 10MB
        maxFiles: 5,
      })
    );
  }

  return logger;
}

export default createLogger;
