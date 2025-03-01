import { StoredEvent } from '../event-store/event-store';
import { Projection, ProjectionRepository, ProjectionHandler } from './projection';
import {
  CampaignCreatedEvent,
  CampaignUpdatedEvent,
  CampaignScheduledEvent,
  CampaignSendingStartedEvent,
  CampaignPausedEvent,
  CampaignCanceledEvent,
  CampaignCompletedEvent,
  CampaignFailedEvent,
} from '../../domain/events/campaign-events';

/**
 * Campaign read model
 */
export interface CampaignReadModel {
  id: string;
  name: string;
  description: string;
  subject: string;
  contentType: 'html' | 'text';
  fromName: string;
  fromEmail: string;
  replyToEmail: string | null;
  status: string;
  createdAt: Date;
  updatedAt: Date;
  scheduledAt: Date | null;
  sentAt: Date | null;
  completedAt: Date | null;
  segmentId: string | null;
  templateId: string | null;
  metadata: Record<string, any>;
  stats?: {
    recipients: number;
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    bounced: number;
    complaints: number;
    unsubscribed: number;
  };
  version: number;
}

/**
 * Campaign projection for building campaign read models
 */
export class CampaignProjection implements Projection<CampaignReadModel> {
  public readonly name = 'campaign-projection';
  public readonly eventTypes = [
    'campaign.created',
    'campaign.updated',
    'campaign.scheduled',
    'campaign.sending.started',
    'campaign.paused',
    'campaign.canceled',
    'campaign.completed',
    'campaign.failed',
  ];

  private handlers: Map<string, ProjectionHandler<CampaignReadModel>> = new Map();

  constructor(private repository: ProjectionRepository<CampaignReadModel>) {
    // Register event handlers
    this.registerHandler(new CampaignCreatedEventHandler());
    this.registerHandler(new CampaignUpdatedEventHandler());
    this.registerHandler(new CampaignScheduledEventHandler());
    this.registerHandler(new CampaignSendingStartedEventHandler());
    this.registerHandler(new CampaignPausedEventHandler());
    this.registerHandler(new CampaignCanceledEventHandler());
    this.registerHandler(new CampaignCompletedEventHandler());
    this.registerHandler(new CampaignFailedEventHandler());
  }

  /**
   * Register a handler for an event type
   */
  private registerHandler(handler: ProjectionHandler<CampaignReadModel>): void {
    this.handlers.set(handler.eventType, handler);
  }

  /**
   * Apply an event to the projection
   */
  public async apply(event: StoredEvent): Promise<void> {
    const handler = this.handlers.get(event.type);

    if (!handler) {
      throw new Error(`No handler registered for event type: ${event.type}`);
    }

    await handler.handle(event, this.repository);
  }

  /**
   * Get a campaign by ID
   */
  public async get(id: string): Promise<CampaignReadModel | null> {
    return this.repository.get(id);
  }

  /**
   * Find campaigns by query
   */
  public async find(query: object): Promise<CampaignReadModel[]> {
    return this.repository.find(query);
  }

  /**
   * Count campaigns by query
   */
  public async count(query: object): Promise<number> {
    return this.repository.count(query);
  }

  /**
   * Reset the projection
   */
  public async reset(): Promise<void> {
    await this.repository.clear();
  }
}

/**
 * Handler for campaign.created events
 */
class CampaignCreatedEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.created';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignCreatedEvent;

    const campaign: CampaignReadModel = {
      id: campaignEvent.aggregateId,
      name: campaignEvent.name,
      description: campaignEvent.description,
      subject: campaignEvent.subject,
      contentType: campaignEvent.contentType,
      fromName: campaignEvent.fromName,
      fromEmail: campaignEvent.fromEmail,
      replyToEmail: campaignEvent.replyToEmail,
      status: 'DRAFT',
      createdAt: campaignEvent.timestamp,
      updatedAt: campaignEvent.timestamp,
      scheduledAt: null,
      sentAt: null,
      completedAt: null,
      segmentId: campaignEvent.segmentId,
      templateId: campaignEvent.templateId,
      metadata: campaignEvent.metadata || {},
      stats: {
        recipients: 0,
        sent: 0,
        delivered: 0,
        opened: 0,
        clicked: 0,
        bounced: 0,
        complaints: 0,
        unsubscribed: 0,
      },
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, campaign);
  }
}

/**
 * Handler for campaign.updated events
 */
class CampaignUpdatedEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.updated';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignUpdatedEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      name: campaignEvent.name,
      description: campaignEvent.description,
      subject: campaignEvent.subject,
      contentType: campaignEvent.contentType,
      fromName: campaignEvent.fromName,
      fromEmail: campaignEvent.fromEmail,
      replyToEmail: campaignEvent.replyToEmail,
      segmentId: campaignEvent.segmentId,
      templateId: campaignEvent.templateId,
      metadata: campaignEvent.metadata,
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}

/**
 * Handler for campaign.scheduled events
 */
class CampaignScheduledEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.scheduled';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignScheduledEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      status: 'SCHEDULED',
      scheduledAt: campaignEvent.scheduledAt,
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}

/**
 * Handler for campaign.sending.started events
 */
class CampaignSendingStartedEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.sending.started';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignSendingStartedEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      status: 'SENDING',
      sentAt: campaignEvent.sentAt,
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}

/**
 * Handler for campaign.paused events
 */
class CampaignPausedEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.paused';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignPausedEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      status: 'PAUSED',
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}

/**
 * Handler for campaign.canceled events
 */
class CampaignCanceledEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.canceled';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignCanceledEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      status: 'CANCELED',
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}

/**
 * Handler for campaign.completed events
 */
class CampaignCompletedEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.completed';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignCompletedEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      status: 'COMPLETED',
      completedAt: campaignEvent.completedAt,
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}

/**
 * Handler for campaign.failed events
 */
class CampaignFailedEventHandler extends ProjectionHandler<CampaignReadModel> {
  public readonly eventType = 'campaign.failed';

  public async handle(event: StoredEvent, repository: ProjectionRepository<CampaignReadModel>): Promise<void> {
    const campaignEvent = event.data as CampaignFailedEvent;
    const campaign = await repository.get(campaignEvent.aggregateId);

    if (!campaign) {
      throw new Error(`Campaign not found: ${campaignEvent.aggregateId}`);
    }

    const updatedCampaign: CampaignReadModel = {
      ...campaign,
      status: 'FAILED',
      metadata: {
        ...campaign.metadata,
        failureReason: campaignEvent.reason,
        failedAt: campaignEvent.timestamp.toISOString(),
      },
      updatedAt: campaignEvent.timestamp,
      version: campaignEvent.version,
    };

    await repository.save(campaignEvent.aggregateId, updatedCampaign);
  }
}
