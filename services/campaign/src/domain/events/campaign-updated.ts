/**
 * Campaign Updated Event
 */

import { BaseDomainEvent } from './domain-event';
import { CampaignId } from '../common/identifiers';
import { CampaignStatus } from '../common/enums';

/**
 * Event data for campaign update
 */
export interface CampaignUpdatedEventData {
  /**
   * Campaign ID
   */
  campaignId: CampaignId;

  /**
   * Campaign name
   */
  name: string;

  /**
   * Update timestamp
   */
  timestamp: Date;

  /**
   * Fields that were updated
   */
  updatedFields: string[];

  /**
   * New status (if status was updated)
   */
  status?: CampaignStatus;
}

/**
 * Campaign Updated Event
 */
export class CampaignUpdatedEvent extends BaseDomainEvent {
  /**
   * Create a new campaign updated event
   * @param data Event data
   */
  constructor(data: CampaignUpdatedEventData) {
    super('campaign.updated', {
      campaignId: data.campaignId.value,
      name: data.name,
      updatedFields: data.updatedFields,
      status: data.status,
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
   * Get updated fields
   */
  public get updatedFields(): string[] {
    return this.payload.updatedFields;
  }

  /**
   * Get new status if updated
   */
  public get status(): CampaignStatus | undefined {
    return this.payload.status;
  }

  /**
   * Check if a specific field was updated
   * @param field Field name
   * @returns Whether the field was updated
   */
  public wasFieldUpdated(field: string): boolean {
    return this.payload.updatedFields.includes(field);
  }
}
