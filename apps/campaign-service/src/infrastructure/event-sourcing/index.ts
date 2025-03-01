import { EventStore, StoredEvent } from '../../event-sourcing/event-store/event-store';
import { Projection, ProjectionManager } from '../../event-sourcing/projections/projection';
import { CampaignProjection, CampaignReadModel } from '../../event-sourcing/projections/campaign-projection';
import { CampaignRepository } from '../../domain/repositories/campaign-repository';
import { PostgresEventStore } from './postgres-event-store';
import { PostgresProjectionRepository } from './postgres-projection-repository';
import { EventSourcingCampaignRepository } from './campaign-repository';
import { InMemoryProjectionManager } from './projection-manager';
import config from '../../config';
import logger from '../logging/logger';

// Singleton instances
let eventStore: EventStore;
let projectionManager: ProjectionManager;
let campaignRepository: CampaignRepository;
let campaignProjectionRepository: PostgresProjectionRepository<CampaignReadModel>;

/**
 * Initialize the event store
 */
export async function initializeEventStore(): Promise<EventStore> {
  if (!eventStore) {
    logger.info('Initializing PostgreSQL event store...');

    eventStore = new PostgresEventStore({
      connectionString: config.eventStore.connectionString,
      schema: config.eventStore.schema,
    });

    // Initialize tables
    await (eventStore as PostgresEventStore).initialize();
  }

  return eventStore;
}

/**
 * Initialize projections
 */
export async function initializeProjections(eventStoreInstance: EventStore): Promise<ProjectionManager> {
  if (!projectionManager) {
    logger.info('Initializing projection manager...');

    // Create projection repositories
    campaignProjectionRepository = new PostgresProjectionRepository<CampaignReadModel>({
      connectionString: config.database.url,
      schema: config.database.schema,
      tableName: 'campaign_projections',
    });

    // Initialize tables
    await campaignProjectionRepository.initialize();

    // Create projections
    const campaignProjection = new CampaignProjection(campaignProjectionRepository);

    // Create projection manager
    projectionManager = new InMemoryProjectionManager(eventStoreInstance);

    // Register projections
    projectionManager.register(campaignProjection);
  }

  return projectionManager;
}

/**
 * Get the event-sourced campaign repository
 */
export function getEventStoreRepository(): CampaignRepository {
  if (!campaignRepository) {
    logger.info('Creating event-sourced campaign repository...');

    if (!eventStore) {
      throw new Error('Event store must be initialized first');
    }

    campaignRepository = new EventSourcingCampaignRepository(eventStore);
  }

  return campaignRepository;
}

/**
 * Get the campaign projection repository
 */
export function getProjectionRepository(): PostgresProjectionRepository<CampaignReadModel> {
  if (!campaignProjectionRepository) {
    throw new Error('Projections must be initialized first');
  }

  return campaignProjectionRepository;
}
