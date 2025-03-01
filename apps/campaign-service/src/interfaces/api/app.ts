import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import bodyParser from 'body-parser';
import morgan from 'morgan';
import { Router } from 'express';
import { setupCampaignRoutes } from './routes/campaign.routes';
import { CommandBus } from '../../application/commands/command';
import { QueryBus } from '../../application/queries/query';
import logger from '../../infrastructure/logging/logger';
import config from '../../config';

/**
 * Create Express application with all middleware and routes
 */
export function createApp(commandBus: CommandBus, queryBus: QueryBus) {
  const app = express();

  // Set security headers
  app.use(helmet());

  // Enable CORS
  app.use(
    cors({
      origin: config.server.corsOrigins,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
      allowedHeaders: ['Content-Type', 'Authorization'],
    })
  );

  // Parse JSON request body
  app.use(bodyParser.json({ limit: '10mb' }));

  // Parse URL-encoded request body
  app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

  // Compress responses
  app.use(compression());

  // HTTP request logging
  app.use(morgan('combined', { stream: logger.stream }));

  // API routes
  const apiRouter = Router();
  setupCampaignRoutes(apiRouter, commandBus, queryBus);
  app.use(config.server.apiPrefix, apiRouter);

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.status(200).json({
      status: 'ok',
      service: 'campaign-service',
      version: process.env.npm_package_version || '1.0.0',
      timestamp: new Date().toISOString(),
    });
  });

  // Not found handler
  app.use((req, res) => {
    res.status(404).json({
      error: `Route ${req.originalUrl} not found`,
      code: 'ROUTE_NOT_FOUND',
    });
  });

  // Error handler
  app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    logger.error('Unhandled error', { error: err.message, stack: err.stack });

    res.status(500).json({
      error: config.isProduction ? 'Internal server error' : err.message,
      code: 'INTERNAL_SERVER_ERROR',
      ...(config.isDevelopment && { stack: err.stack }),
    });
  });

  return app;
}
