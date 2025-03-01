import winston from 'winston';
import path from 'path';
import fs from 'fs';
import config from '../config';

// Ensure log directory exists
const logDir = path.dirname(config.logging.filePath);
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Define custom log format
const customFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ timestamp, level, message, service, ...meta }) => {
    const metaString = Object.keys(meta).length
      ? `\n${JSON.stringify(meta, null, 2)}`
      : '';

    return `[${timestamp}] ${level.toUpperCase()} [${service || 'analytics-service'}]: ${message}${metaString}`;
  })
);

// Define transports
const transports: winston.transport[] = [
  // Console transport for all environments
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize({ all: true }),
      customFormat
    ),
  }),
];

// Add file transport for non-test environments
if (config.env !== 'test') {
  transports.push(
    new winston.transports.File({
      filename: config.logging.filePath,
      format: customFormat,
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
    })
  );
}

// Create the logger
const logger = winston.createLogger({
  level: config.logging.level,
  defaultMeta: {
    service: 'analytics-service',
    env: config.env,
  },
  transports,
  exitOnError: false,
});

// Export named functions for easier usage
export default {
  error: (message: string, meta: Record<string, any> = {}) => {
    logger.error(message, meta);
  },

  warn: (message: string, meta: Record<string, any> = {}) => {
    logger.warn(message, meta);
  },

  info: (message: string, meta: Record<string, any> = {}) => {
    logger.info(message, meta);
  },

  debug: (message: string, meta: Record<string, any> = {}) => {
    logger.debug(message, meta);
  },

  // Express middleware for HTTP request logging
  httpLogger: () => {
    return (req: any, res: any, next: () => void) => {
      const startTime = new Date().getTime();

      res.on('finish', () => {
        const responseTime = new Date().getTime() - startTime;
        const statusCode = res.statusCode;
        const method = req.method;
        const url = req.originalUrl || req.url;
        const userAgent = req.get('user-agent') || '';
        const contentLength = res.get('content-length') || 0;

        const message = `${method} ${url} ${statusCode} ${responseTime}ms - ${contentLength}`;

        const meta = {
          method,
          url,
          statusCode,
          responseTime,
          contentLength,
          userAgent,
          ip: req.ip || req.connection.remoteAddress,
        };

        if (statusCode >= 500) {
          logger.error(message, meta);
        } else if (statusCode >= 400) {
          logger.warn(message, meta);
        } else {
          logger.info(message, meta);
        }
      });

      next();
    };
  },

  // Stream for Morgan integration
  stream: {
    write: (message: string) => {
      logger.info(message.trim());
    },
  },
};
