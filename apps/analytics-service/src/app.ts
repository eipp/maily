import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import bodyParser from 'body-parser';
import promBundle from 'express-prom-bundle';
import config from './config';
import logger from './utils/logger';
import eventsRoutes from './routes/events.routes';
import predictiveRoutes from './routes/predictive.routes';

// Create Express application
const app = express();

// Set security headers
app.use(helmet());

// Enable CORS
app.use(cors());

// Compress responses
app.use(compression());

// Parse JSON requests
app.use(bodyParser.json({ limit: '10mb' }));

// Parse URL-encoded requests
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// HTTP request logging
app.use(morgan('combined', { stream: logger.stream }));

// Prometheus metrics middleware (if enabled)
if (config.metrics.enabled) {
  const metricsMiddleware = promBundle({
    includeMethod: true,
    includePath: true,
    includeStatusCode: true,
    includeUp: true,
    promClient: {
      collectDefaultMetrics: {
        timeout: 5000,
      },
    },
  });
  app.use(metricsMiddleware);
}

// API routes
app.use(`${config.server.apiPrefix}/events`, eventsRoutes);
app.use(`${config.server.apiPrefix}/predictive`, predictiveRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    service: 'analytics-service',
    version: process.env.npm_package_version || '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

// API documentation endpoint
app.get(`${config.server.apiPrefix}/docs`, (req, res) => {
  res.redirect('/api-docs');
});

// Not found handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: `Route ${req.originalUrl} not found`,
  });
});

// Error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error('Unhandled error', { error: err.message, stack: err.stack });

  res.status(500).json({
    success: false,
    message: config.isProduction ? 'Internal server error' : err.message,
    ...(config.isDevelopment && { stack: err.stack }),
  });
});

export default app;
