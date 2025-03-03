/**
 * Campaign Completed Event
 */

import { BaseDomainEvent } from './domain-event';
import { CampaignId } from '../common/identifiers';

/**
 * Event data for campaign completion
 */
export interface CampaignCompletedEventData {
  /**
   * Campaign ID
   */
  campaignId: CampaignId;

  /**
   * Campaign name
   */
  name: string;

  /**
   * Completion timestamp
   */
  timestamp: Date;

  /**
   * Number of emails sent
   */
  sentCount: number;

  /**
   * Number of emails opened
   */
  openCount: number;

  /**
   * Number of email clicks
   */
  clickCount: number;

  /**
   * Number of email bounces
   */
  bounceCount: number;

  /**
   * Number of email complaints
   */
  complaintCount: number;
}

/**
 * Campaign Completed Event
 */
export class CampaignCompletedEvent extends BaseDomainEvent {
  /**
   * Create a new campaign completed event
   * @param data Event data
   */
  constructor(data: CampaignCompletedEventData) {
    super('campaign.completed', {
      campaignId: data.campaignId.value,
      name: data.name,
      sentCount: data.sentCount,
      openCount: data.openCount,
      clickCount: data.clickCount,
      bounceCount: data.bounceCount,
      complaintCount: data.complaintCount,
      openRate: data.sentCount > 0 ? data.openCount / data.sentCount : 0,
      clickRate: data.sentCount > 0 ? data.clickCount / data.sentCount : 0,
      bounceRate: data.sentCount > 0 ? data.bounceCount / data.sentCount : 0,
      complaintRate: data.sentCount > 0 ? data.complaintCount / data.sentCount : 0,
      clickToOpenRate: data.openCount > 0 ? data.clickCount / data.openCount : 0,
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
   * Get number of emails sent
   */
  public get sentCount(): number {
    return this.payload.sentCount;
  }

  /**
   * Get number of emails opened
   */
  public get openCount(): number {
    return this.payload.openCount;
  }

  /**
   * Get number of email clicks
   */
  public get clickCount(): number {
    return this.payload.clickCount;
  }

  /**
   * Get number of email bounces
   */
  public get bounceCount(): number {
    return this.payload.bounceCount;
  }

  /**
   * Get number of email complaints
   */
  public get complaintCount(): number {
    return this.payload.complaintCount;
  }

  /**
   * Get email open rate
   */
  public get openRate(): number {
    return this.payload.openRate;
  }

  /**
   * Get email click rate
   */
  public get clickRate(): number {
    return this.payload.clickRate;
  }

  /**
   * Get email bounce rate
   */
  public get bounceRate(): number {
    return this.payload.bounceRate;
  }

  /**
   * Get email complaint rate
   */
  public get complaintRate(): number {
    return this.payload.complaintRate;
  }

  /**
   * Get click-to-open rate
   */
  public get clickToOpenRate(): number {
    return this.payload.clickToOpenRate;
  }
}
