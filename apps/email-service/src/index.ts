/**
 * Email Service Main Entry Point
 */
import 'reflect-metadata';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { createServer } from 'http';
import { DataSource } from 'typeorm';
import { Redis } from 'ioredis';
import { Registry, collectDefaultMetrics } from 'prom-client';
import { config } from 'dotenv';

// Import domain and application layer
import { EmailService } from './application/usecases/email-service';

// Import infrastructure layer
import { EmailEntity } from './infrastructure/entities/email.entity';
import { TypeOrmEmailRepository } from './infrastructure/repositories/email-repository';
import { PrometheusEmailMetrics } from './infrastructure/metrics/email-metrics';
import { RedisEmailRateLimiter } from './infrastructure/rate-limiting/redis-rate-limiter';

// Import adapters layer
import { EmailProviderFactory } from './adapters/factories/provider-factory';
import { EmailController } from './adapters/api/email-controller';

// Load environment variables
config();

// Initialize Express application
const app = express();
const server = createServer(app);
const port = process.env.PORT || 8080;

// Prometheus registry for metrics
const registry = new Registry();
collectDefaultMetrics({ register: registry });

// Configure middleware
app.use(express.json({ limit: '10mb' }));

// CORS configuration with justmaily.com domains
app.use(cors({
  origin: [
    `https://${process.env.MAIN_DOMAIN || 'justmaily.com'}`,
    `https://${process.env.APP_DOMAIN || 'app.justmaily.com'}`,
    `https://${process.env.CONSOLE_DOMAIN || 'console.justmaily.com'}`
  ],
  credentials: true
}));
app.use(helmet());
app.use(morgan('combined'));

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});

// Database configuration
const dataSource = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  username: process.env.DB_USERNAME || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
  database: process.env.DB_DATABASE || 'email_service',
  entities: [EmailEntity],
  synchronize: process.env.NODE_ENV !== 'production', // Should be false in production, use migrations
  logging: process.env.NODE_ENV !== 'production'
});

// Redis client for rate limiting
const redisClient = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  db: parseInt(process.env.REDIS_DB || '0')
});

// Rate limiting configuration
const rateLimits: Record<string, number> = {
  resend: parseInt(process.env.RATE_LIMIT_RESEND || '1000'),
  sendgrid: parseInt(process.env.RATE_LIMIT_SENDGRID || '1000'),
  mailgun: parseInt(process.env.RATE_LIMIT_MAILGUN || '1000'),
};

// Application startup
async function bootstrap() {
  try {
    // Connect to database
    await dataSource.initialize();
    console.log('Database connection initialized');

    // Initialize repositories
    const emailRepository = new TypeOrmEmailRepository(
      dataSource.getRepository(EmailEntity)
    );

    // Initialize metrics service
    const metricsService = new PrometheusEmailMetrics(registry);

    // Initialize rate limiter
    const rateLimiter = new RedisEmailRateLimiter(
      redisClient,
      rateLimits
    );

    // Create email provider based on configuration
    const emailProvider = EmailProviderFactory.createProvider({
      type: (process.env.EMAIL_PROVIDER_TYPE || 'resend') as any,
      apiKey: process.env.EMAIL_PROVIDER_API_KEY || '',
      domain: process.env.EMAIL_PROVIDER_DOMAIN,
      region: process.env.EMAIL_PROVIDER_REGION as any
    });

    // Create email service
    const emailService = new EmailService(
      emailProvider,
      emailRepository,
      metricsService,
      rateLimiter
    );

    // Initialize controllers
    const emailController = new EmailController(emailService);

    // Configure routes
    app.use('/api/emails', emailController.getRouter());

    // Global error handler
    app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
      console.error('Unhandled error:', err);
      res.status(500).json({
        success: false,
        error: process.env.NODE_ENV === 'production'
          ? 'Internal server error'
          : err.message || 'Unknown error'
      });
    });

    // Start server
    server.listen(port, () => {
      console.log(`Email service running on http://localhost:${port}`);
    });

    // Handle graceful shutdown
    const shutdown = async () => {
      console.log('Shutting down gracefully...');

      // Close server first (stop accepting new requests)
      await new Promise<void>((resolve) => {
        server.close(() => resolve());
      });

      // Close database connection
      await dataSource.destroy();

      // Close Redis connection
      await redisClient.quit();

      console.log('Shutdown complete');
      process.exit(0);
    };

    // Register shutdown handlers
    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
  } catch (error) {
    console.error('Failed to start application:', error);
    process.exit(1);
  }
}

// Start the application
bootstrap();
