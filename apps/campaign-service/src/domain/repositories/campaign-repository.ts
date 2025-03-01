import { Campaign } from '../entities/campaign';
import { ID } from '../value-objects/id';
import { CampaignEventType } from '../events/campaign-events';

/**
 * Repository interface for the Campaign aggregate
 */
export interface CampaignRepository {
  /**
   * Find a campaign by ID
   * @param id Campaign ID
   */
  findById(id: ID): Promise<Campaign | null>;

  /**
   * Find campaigns by criteria
   * @param criteria Search criteria
   * @param options Additional options like pagination
   */
  findByCriteria(
    criteria: CampaignSearchCriteria,
    options?: CampaignSearchOptions
  ): Promise<CampaignSearchResult>;

  /**
   * Save a campaign
   * @param campaign Campaign to save
   * @param expectedVersion Optional expected version for optimistic concurrency
   */
  save(campaign: Campaign, expectedVersion?: number): Promise<void>;

  /**
   * Delete a campaign
   * @param id Campaign ID
   */
  delete(id: ID): Promise<void>;

  /**
   * Get events for a campaign
   * @param id Campaign ID
   */
  getEvents(id: ID): Promise<CampaignEventType[]>;
}

/**
 * Campaign search criteria
 */
export interface CampaignSearchCriteria {
  ids?: ID[];
  name?: string;
  status?: string | string[];
  createdAfter?: Date;
  createdBefore?: Date;
  scheduledAfter?: Date;
  scheduledBefore?: Date;
  sentAfter?: Date;
  sentBefore?: Date;
  segmentId?: ID;
  fromEmail?: string;
}

/**
 * Campaign search options
 */
export interface CampaignSearchOptions {
  skip?: number;
  limit?: number;
  sortBy?: string;
  sortDirection?: 'ASC' | 'DESC';
}

/**
 * Campaign search result
 */
export interface CampaignSearchResult {
  items: Campaign[];
  total: number;
  skip: number;
  limit: number;
}
