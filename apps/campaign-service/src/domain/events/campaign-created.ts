/**
 * Campaign Created Event
 */

import { BaseDomainEvent } from './domain-event';
import { CampaignId, UserId } from '../common/identifiers';
import { CampaignType } from '../common/enums';

/**
 * Event data for campaign creation
 */
export interface CampaignCreatedEventData {
  /**
   * Campaign ID
   */
  campaignId: CampaignId;

  /**
   * Campaign name
   */
  name: string;

  /**
   * Campaign type
   */
  type: CampaignType;

  /**
   * User who created the campaign
   */
  createdBy: UserId;

  /**
   * Creation timestamp
   */
  timestamp: Date;
}

/**
 * Campaign Created Event
 */
export class CampaignCreatedEvent extends BaseDomainEvent {
  /**
   * Create a new campaign created event
   * @param data Event data
   */
  constructor(data: CampaignCreatedEventData) {
    super('campaign.created', {
      campaignId: data.campaignId.value,
      name: data.name,
      type: data.type,
      createdBy: data.createdBy.value,
    }, data.timestamp);
  }

  /**
   * Get campaign ID
   */
  public get campaignId(): string {
    return this.payload.campaignId;
  }

  /**
   * Get campaign name
   */
  public get name(): string {
    return this.payload.name;
  }

  /**
   * Get campaign type
   */
  public get type(): CampaignType {
    return this.payload.type;
  }

  /**
   * Get user who created the campaign
   */
  public get createdBy(): string {
    return this.payload.createdBy;
  }
}
