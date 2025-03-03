/**
 * Campaign Canceled Event
 */

import { BaseDomainEvent } from './domain-event';
import { CampaignId } from '../common/identifiers';

/**
 * Event data for campaign cancellation
 */
export interface CampaignCanceledEventData {
  /**
   * Campaign ID
   */
  campaignId: CampaignId;

  /**
   * Campaign name
   */
  name: string;

  /**
   * Cancellation timestamp
   */
  timestamp: Date;

  /**
   * Number of emails sent before cancellation
   */
  sentCount: number;
}

/**
 * Campaign Canceled Event
 */
export class CampaignCanceledEvent extends BaseDomainEvent {
  /**
   * Create a new campaign canceled event
   * @param data Event data
   */
  constructor(data: CampaignCanceledEventData) {
    super('campaign.canceled', {
      campaignId: data.campaignId.value,
      name: data.name,
      sentCount: data.sentCount,
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
   * Get number of emails sent before cancellation
   */
  public get sentCount(): number {
    return this.payload.sentCount;
  }
}
