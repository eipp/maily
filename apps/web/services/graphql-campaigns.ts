import { ApolloError } from '@apollo/client';
import {
  GET_CAMPAIGNS,
  GET_CAMPAIGN,
  GET_CAMPAIGN_STATS
} from '@/graphql/queries';
import {
  CREATE_CAMPAIGN,
  UPDATE_CAMPAIGN,
  DELETE_CAMPAIGN,
  SEND_CAMPAIGN,
  SCHEDULE_CAMPAIGN
} from '@/graphql/mutations';
import { executeQuery, executeMutation } from '@/lib/apollo-server';

/**
 * Campaigns GraphQL Service
 * Provides functions for interacting with campaign data through GraphQL
 */

// Interfaces
export interface CampaignStats {
  sent: number;
  opened: number;
  clicked: number;
  bounced?: number;
  unsubscribed?: number;
}

export interface CampaignTemplate {
  id: string;
  name: string;
}

export interface CampaignSegment {
  id: string;
  name: string;
  count: number;
}

export interface Campaign {
  id: string;
  name: string;
  subject: string;
  previewText?: string;
  fromName: string;
  fromEmail: string;
  replyToEmail: string;
  status: string;
  createdAt: string;
  scheduledFor?: string;
  sentAt?: string;
  trackOpens: boolean;
  trackClicks: boolean;
  template?: CampaignTemplate;
  segment?: CampaignSegment;
  stats: CampaignStats;
}

export interface DailyStats {
  date: string;
  opens: number;
  clicks: number;
}

export interface DeviceStats {
  device: string;
  count: number;
}

export interface LocationStats {
  country: string;
  count: number;
}

export interface LinkStats {
  url: string;
  clicks: number;
}

export interface DetailedCampaignStats {
  dailyStats: DailyStats[];
  deviceStats: DeviceStats[];
  locationStats: LocationStats[];
  linkStats: LinkStats[];
}

// Response interfaces
export interface CampaignsData {
  campaigns: Campaign[];
}

export interface CampaignData {
  campaign: Campaign;
}

export interface CampaignStatsData {
  campaignStats: DetailedCampaignStats;
}

// Input interfaces
export interface CampaignInput {
  name: string;
  subject: string;
  previewText?: string;
  templateId: string;
  segmentId: string;
  fromName: string;
  fromEmail: string;
  replyToEmail: string;
  trackOpens?: boolean;
  trackClicks?: boolean;
}

/**
 * Fetch campaigns list with optional pagination
 */
export async function getCampaigns(
  page: number = 1,
  pageSize: number = 10
): Promise<Campaign[]> {
  try {
    const data = await executeQuery<CampaignsData>(GET_CAMPAIGNS, {
      page,
      pageSize
    });
    return data.campaigns;
  } catch (error) {
    console.error('Failed to fetch campaigns:', error);
    throw error;
  }
}

/**
 * Fetch a single campaign by ID
 */
export async function getCampaign(id: string): Promise<Campaign | null> {
  try {
    const data = await executeQuery<CampaignData>(GET_CAMPAIGN, { id });
    return data.campaign;
  } catch (error) {
    if (error instanceof ApolloError && error.message.includes('not found')) {
      return null;
    }
    console.error(`Failed to fetch campaign ${id}:`, error);
    throw error;
  }
}

/**
 * Fetch detailed statistics for a campaign
 */
export async function getCampaignStats(id: string): Promise<DetailedCampaignStats> {
  try {
    const data = await executeQuery<CampaignStatsData>(GET_CAMPAIGN_STATS, { id });
    return data.campaignStats;
  } catch (error) {
    console.error(`Failed to fetch stats for campaign ${id}:`, error);
    throw error;
  }
}

/**
 * Create a new campaign
 */
export async function createCampaign(campaign: CampaignInput): Promise<Campaign> {
  try {
    const response = await executeMutation<{ createCampaign: Campaign }>(
      CREATE_CAMPAIGN,
      campaign
    );
    return response.createCampaign;
  } catch (error) {
    console.error('Failed to create campaign:', error);
    throw error;
  }
}

/**
 * Update an existing campaign
 */
export async function updateCampaign(
  id: string,
  campaign: Partial<CampaignInput>
): Promise<Campaign> {
  try {
    const response = await executeMutation<{ updateCampaign: Campaign }>(
      UPDATE_CAMPAIGN,
      { id, ...campaign }
    );
    return response.updateCampaign;
  } catch (error) {
    console.error(`Failed to update campaign ${id}:`, error);
    throw error;
  }
}

/**
 * Delete a campaign
 */
export async function deleteCampaign(id: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await executeMutation<{
      deleteCampaign: { success: boolean; message: string }
    }>(DELETE_CAMPAIGN, { id });
    return response.deleteCampaign;
  } catch (error) {
    console.error(`Failed to delete campaign ${id}:`, error);
    throw error;
  }
}

/**
 * Send a campaign immediately
 */
export async function sendCampaign(id: string): Promise<Campaign> {
  try {
    const response = await executeMutation<{ sendCampaign: Campaign }>(
      SEND_CAMPAIGN,
      { id }
    );
    return response.sendCampaign;
  } catch (error) {
    console.error(`Failed to send campaign ${id}:`, error);
    throw error;
  }
}

/**
 * Schedule a campaign for later sending
 */
export async function scheduleCampaign(
  id: string,
  scheduledFor: string
): Promise<Campaign> {
  try {
    const response = await executeMutation<{ scheduleCampaign: Campaign }>(
      SCHEDULE_CAMPAIGN,
      { id, scheduledFor }
    );
    return response.scheduleCampaign;
  } catch (error) {
    console.error(`Failed to schedule campaign ${id}:`, error);
    throw error;
  }
}
