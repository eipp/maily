/**
 * Campaign Paused Event
 */

import { BaseDomainEvent } from './domain-event';
import { CampaignId } from '../common/identifiers';

/**
 * Event data for campaign pause
 */
export interface CampaignPausedEventData {
  /**
   * Campaign ID
   */
  campaignId: CampaignId;

  /**
   * Campaign name
   */
  name: string;

  /**
   * Pause timestamp
   */
  timestamp: Date;

  /**
   * Number of emails sent before pausing
   */
  sentCount: number;
}

/**
 * Campaign Paused Event
 */
export class CampaignPausedEvent extends BaseDomainEvent {
  /**
   * Create a new campaign paused event
   * @param data Event data
   */
  constructor(data: CampaignPausedEventData) {
    super('campaign.paused', {
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
   * Get number of emails sent before pausing
   */
  public get sentCount(): number {
    return this.payload.sentCount;
  }
}
