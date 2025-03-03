import { Identifier } from '../common/Identifier';

/**
 * Unique identifier for Campaign entities.
 */
export class CampaignId extends Identifier {
  constructor(id: string) {
    super(id);
  }
  
  /**
   * Creates a new CampaignId instance.
   */
  public static create(id: string): CampaignId {
    return new CampaignId(id);
  }
}

/**
 * Campaign analytics data.
 */
export interface CampaignAnalytics {
  /**
   * Number of emails sent.
   */
  sent: number;
  
  /**
   * Number of emails delivered.
   */
  delivered: number;
  
  /**
   * Number of emails opened.
   */
  opened: number;
  
  /**
   * Number of unique opens.
   */
  uniqueOpens: number;
  
  /**
   * Number of clicks on links in the campaign.
   */
  clicks: number;
  
  /**
   * Number of unique clicks.
   */
  uniqueClicks: number;
  
  /**
   * Number of recipients who unsubscribed through the campaign.
   */
  unsubscribes: number;
  
  /**
   * Number of recipients who reported the campaign as spam.
   */
  complaints: number;
  
  /**
   * Number of bounces.
   */
  bounces: number;
}

/**
 * Campaign type classification.
 */
export enum CampaignType {
  REGULAR = 'REGULAR',
  AUTOMATED = 'AUTOMATED',
  AB_TEST = 'AB_TEST',
  DRIP = 'DRIP',
  TRANSACTIONAL = 'TRANSACTIONAL'
}