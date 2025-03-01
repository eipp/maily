/**
 * Campaign Launched Event
 */

import { BaseDomainEvent } from './domain-event';
import { CampaignId } from '../common/identifiers';

/**
 * Event data for campaign launch
 */
export interface CampaignLaunchedEventData {
  /**
   * Campaign ID
   */
  campaignId: CampaignId;

  /**
   * Campaign name
   */
  name: string;

  /**
   * Launch timestamp
   */
  timestamp: Date;

  /**
   * Size of the audience
   */
  audienceSize: number;
}

/**
 * Campaign Launched Event
 */
export class CampaignLaunchedEvent extends BaseDomainEvent {
  /**
   * Create a new campaign launched event
   * @param data Event data
   */
  constructor(data: CampaignLaunchedEventData) {
    super('campaign.launched', {
      campaignId: data.campaignId.value,
      name: data.name,
      audienceSize: data.audienceSize,
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
   * Get audience size
   */
  public get audienceSize(): number {
    return this.payload.audienceSize;
  }
}
