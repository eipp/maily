import app from './app';
import config from './config';
import logger from './utils/logger';
import { connectDatabase, closeDatabase } from './utils/db';
import { RabbitMQSubscriber } from './events/rabbitmq';
import eventProcessor from './processors/event-processor';
import http from 'http';

// Server instance
let server: http.Server | null = null;

// Event subscriber instance
let eventSubscriber: RabbitMQSubscriber | null = null;

// Graceful shutdown handler
let shuttingDown = false;

const gracefulShutdown = async (signal: string) => {
  if (shuttingDown) return;

  shuttingDown = true;
  logger.info(`Received ${signal}. Starting graceful shutdown...`);

  // Close HTTP server (if applicable)
  if (server) {
    logger.info('Closing HTTP server...');
    server.close();
  }

  try {
    // Disconnect from message broker
    if (eventSubscriber) {
      logger.info('Closing event subscriber...');
      await eventSubscriber.close();
    }

    // Close database connection
    logger.info('Closing database connection...');
    await closeDatabase();

    logger.info('Graceful shutdown completed');
    process.exit(0);
  } catch (error: any) {
    logger.error('Error during graceful shutdown', { error: error.message });
    process.exit(1);
  }
};

// Handle events from the event subscriber
const handleEvent = async (event: any) => {
  try {
    await eventProcessor.processEvent(event);
  } catch (error: any) {
    logger.error('Error processing event from subscriber', {
      eventId: event.id,
      eventType: event.type,
      error: error.message,
    });
  }
};

// Initialize the application
const initialize = async () => {
  try {
    // Connect to MongoDB
    await connectDatabase();

    // Initialize event subscriber
    eventSubscriber = new RabbitMQSubscriber();
    await eventSubscriber.initialize();

    // Subscribe to events
    await eventSubscriber.subscribe('*', handleEvent);

    logger.info('Analytics service initialized successfully');
  } catch (error: any) {
    logger.error('Error initializing analytics service', { error: error.message });
    process.exit(1);
  }
};

// Start the application
const startApp = async (): Promise<void> => {
  try {
    await initialize();

    // Start HTTP server
    server = app.listen(config.server.port, () => {
      logger.info(`Analytics service listening on port ${config.server.port}`);
      logger.info(`Environment: ${config.env}`);
      logger.info(`API prefix: ${config.server.apiPrefix}`);
    });

    // Set up signal handlers for graceful shutdown
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

    // Catch unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled promise rejection', {
        reason: reason instanceof Error ? reason.message : reason,
        stack: reason instanceof Error ? reason.stack : undefined,
      });
    });

    // Catch uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught exception', {
        error: error.message,
        stack: error.stack,
      });

      // Exit with error
      process.exit(1);
    });
  } catch (error: any) {
    logger.error('Error starting analytics service', { error: error.message });
    process.exit(1);
  }
};

// Start the server
startApp().catch((error) => {
  logger.error('Failed to start analytics service', { error: error.message });
  process.exit(1);
});

// Export for testing
export default app;
