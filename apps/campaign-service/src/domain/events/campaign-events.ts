import { ID } from '../value-objects/id';
import { EmailAddress } from '../value-objects/email-address';
import { CampaignStatus, CampaignStatusValue } from '../value-objects/campaign-status';

/**
 * Base interface for all domain events
 */
export interface DomainEvent {
  /**
   * Type of the event
   */
  readonly type: string;

  /**
   * Aggregate ID the event belongs to
   */
  readonly aggregateId: string;

  /**
   * Version of the aggregate after the event
   */
  readonly version: number;

  /**
   * When the event occurred
   */
  readonly timestamp: Date;
}

/**
 * Base class for Campaign domain events
 */
export abstract class CampaignEvent implements DomainEvent {
  public abstract readonly type: string;
  public readonly aggregateId: string;
  public readonly version: number;
  public readonly timestamp: Date;

  constructor(campaignId: string, version: number, timestamp?: Date) {
    this.aggregateId = campaignId;
    this.version = version;
    this.timestamp = timestamp || new Date();
  }
}

/**
 * Event emitted when a new campaign is created
 */
export class CampaignCreatedEvent extends CampaignEvent {
  public readonly type = 'campaign.created';

  constructor(
    campaignId: string,
    public readonly name: string,
    public readonly description: string,
    public readonly subject: string,
    public readonly content: string,
    public readonly contentType: 'html' | 'text',
    public readonly fromName: string,
    public readonly fromEmail: string,
    public readonly replyToEmail: string | null,
    public readonly segmentId: string | null,
    public readonly templateId: string | null,
    public readonly metadata: Record<string, any>,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when campaign details are updated
 */
export class CampaignUpdatedEvent extends CampaignEvent {
  public readonly type = 'campaign.updated';

  constructor(
    campaignId: string,
    public readonly name: string,
    public readonly description: string,
    public readonly subject: string,
    public readonly content: string,
    public readonly contentType: 'html' | 'text',
    public readonly fromName: string,
    public readonly fromEmail: string,
    public readonly replyToEmail: string | null,
    public readonly segmentId: string | null,
    public readonly templateId: string | null,
    public readonly metadata: Record<string, any>,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when a campaign is scheduled
 */
export class CampaignScheduledEvent extends CampaignEvent {
  public readonly type = 'campaign.scheduled';

  constructor(
    campaignId: string,
    public readonly scheduledAt: Date,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when a campaign starts sending
 */
export class CampaignSendingStartedEvent extends CampaignEvent {
  public readonly type = 'campaign.sending.started';

  constructor(
    campaignId: string,
    public readonly sentAt: Date,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when a campaign is paused
 */
export class CampaignPausedEvent extends CampaignEvent {
  public readonly type = 'campaign.paused';

  constructor(
    campaignId: string,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when a campaign is canceled
 */
export class CampaignCanceledEvent extends CampaignEvent {
  public readonly type = 'campaign.canceled';

  constructor(
    campaignId: string,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when a campaign is completed
 */
export class CampaignCompletedEvent extends CampaignEvent {
  public readonly type = 'campaign.completed';

  constructor(
    campaignId: string,
    public readonly completedAt: Date,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Event emitted when a campaign fails
 */
export class CampaignFailedEvent extends CampaignEvent {
  public readonly type = 'campaign.failed';

  constructor(
    campaignId: string,
    public readonly reason: string,
    version: number,
    timestamp?: Date
  ) {
    super(campaignId, version, timestamp);
  }
}

/**
 * Types of all Campaign events
 */
export type CampaignEventType =
  | CampaignCreatedEvent
  | CampaignUpdatedEvent
  | CampaignScheduledEvent
  | CampaignSendingStartedEvent
  | CampaignPausedEvent
  | CampaignCanceledEvent
  | CampaignCompletedEvent
  | CampaignFailedEvent;
