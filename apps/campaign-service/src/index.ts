import { createApp } from './interfaces/api/app';
import { InMemoryCommandBus } from './application/commands/command';
import { InMemoryQueryBus } from './application/queries/query';
import {
  CreateCampaignCommandHandler,
  UpdateCampaignCommandHandler,
  ScheduleCampaignCommandHandler,
  SendCampaignCommandHandler,
  PauseCampaignCommandHandler,
  CancelCampaignCommandHandler,
  CompleteCampaignCommandHandler,
  FailCampaignCommandHandler,
} from './application/commands/campaign-commands';
import {
  GetCampaignByIdQueryHandler,
  ListCampaignsQueryHandler,
  GetCampaignStatsQueryHandler,
  GetCampaignCountsByStatusQueryHandler,
} from './application/queries/campaign-queries';
import {
  initializeEventStore,
  initializeProjections,
  getEventStoreRepository,
  getProjectionRepository,
} from './infrastructure/event-sourcing';
import logger from './infrastructure/logging/logger';
import config from './config';

/**
 * Bootstrap the application
 */
async function bootstrap() {
  try {
    logger.info('Starting Campaign Service...');

    // Initialize event store
    logger.info('Initializing event store...');
    const eventStore = await initializeEventStore();

    // Initialize projections
    logger.info('Initializing projections...');
    const projectionManager = await initializeProjections(eventStore);

    // Get repositories
    const campaignRepository = getEventStoreRepository();
    const campaignProjectionRepository = getProjectionRepository();

    // Create command and query buses
    const commandBus = new InMemoryCommandBus();
    const queryBus = new InMemoryQueryBus();

    // Register command handlers
    logger.info('Registering command handlers...');
    commandBus.register('campaign.create', new CreateCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.update', new UpdateCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.schedule', new ScheduleCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.send', new SendCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.pause', new PauseCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.cancel', new CancelCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.complete', new CompleteCampaignCommandHandler(campaignRepository));
    commandBus.register('campaign.fail', new FailCampaignCommandHandler(campaignRepository));

    // Register query handlers
    logger.info('Registering query handlers...');
    queryBus.register('campaign.getById', new GetCampaignByIdQueryHandler(campaignProjectionRepository));
    queryBus.register('campaign.list', new ListCampaignsQueryHandler(campaignProjectionRepository));
    queryBus.register('campaign.getStats', new GetCampaignStatsQueryHandler(campaignProjectionRepository));
    queryBus.register('campaign.getCountsByStatus', new GetCampaignCountsByStatusQueryHandler(campaignProjectionRepository));

    // Create and configure Express app
    const app = createApp(commandBus, queryBus);

    // Start projections
    logger.info('Starting projections...');
    await projectionManager.startAll();

    // Start server
    const server = app.listen(config.server.port, () => {
      logger.info(`Campaign Service listening on port ${config.server.port}`);
      logger.info(`Environment: ${config.env}`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => shutdown(server));
    process.on('SIGINT', () => shutdown(server));

    logger.info('Campaign Service started successfully');
  } catch (error: any) {
    logger.error('Failed to start Campaign Service', { error: error.message, stack: error.stack });
    process.exit(1);
  }
}

/**
 * Graceful shutdown
 */
async function shutdown(server: any) {
  logger.info('Shutting down Campaign Service...');

  // Close server
  server.close(() => {
    logger.info('HTTP server closed');
  });

  try {
    // Stop projections
    logger.info('Stopping projections...');
    // await projectionManager.stopAll();

    // Close event store
    logger.info('Closing event store...');
    // await eventStore.close();

    logger.info('Campaign Service shut down successfully');
    process.exit(0);
  } catch (error: any) {
    logger.error('Error during shutdown', { error: error.message });
    process.exit(1);
  }
}

// Start the application
bootstrap();
