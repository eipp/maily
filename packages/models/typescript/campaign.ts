/**
 * Campaign models for the Maily platform.
 */
import { z } from 'zod';

/**
 * Campaign status enumeration.
 */
export enum CampaignStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  SENDING = 'sending',
  SENT = 'sent',
  PAUSED = 'paused',
  CANCELLED = 'cancelled',
}

/**
 * Campaign type enumeration.
 */
export enum CampaignType {
  EMAIL = 'email',
  SMS = 'sms',
  PUSH = 'push',
  SOCIAL = 'social',
  MULTICHANNEL = 'multichannel',
}

/**
 * Campaign content data.
 */
export interface CampaignContent {
  subject: string;
  preheader?: string;
  body?: string;
  html?: string;
  templateId?: string;
  variables: Record<string, any>;
  attachments: string[];
}

/**
 * Campaign performance metrics.
 */
export interface CampaignMetrics {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  unsubscribed: number;
  bounced: number;
  complaints: number;
  revenue: number;
  conversionRate: number;
  lastUpdated?: string;
}

/**
 * Campaign model.
 */
export interface Campaign {
  id: string;
  userId: string;
  name: string;
  description?: string;
  status: CampaignStatus;
  type: CampaignType;
  content: CampaignContent;
  segmentId?: string;
  metrics: CampaignMetrics;
  scheduleTime?: string;
  sentTime?: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  metadata: Record<string, any>;
}

/**
 * Campaign content schema for validation.
 */
export const campaignContentSchema = z.object({
  subject: z.string(),
  preheader: z.string().optional(),
  body: z.string().optional(),
  html: z.string().optional(),
  templateId: z.string().optional(),
  variables: z.record(z.any()).default({}),
  attachments: z.array(z.string()).default([]),
});

/**
 * Campaign metrics schema for validation.
 */
export const campaignMetricsSchema = z.object({
  sent: z.number().default(0),
  delivered: z.number().default(0),
  opened: z.number().default(0),
  clicked: z.number().default(0),
  unsubscribed: z.number().default(0),
  bounced: z.number().default(0),
  complaints: z.number().default(0),
  revenue: z.number().default(0),
  conversionRate: z.number().default(0),
  lastUpdated: z.string().optional(),
});

/**
 * Campaign schema for validation.
 */
export const campaignSchema = z.object({
  id: z.string(),
  userId: z.string(),
  name: z.string(),
  description: z.string().optional(),
  status: z.nativeEnum(CampaignStatus).default(CampaignStatus.DRAFT),
  type: z.nativeEnum(CampaignType).default(CampaignType.EMAIL),
  content: campaignContentSchema,
  segmentId: z.string().optional(),
  metrics: campaignMetricsSchema.default({}),
  scheduleTime: z.string().optional(),
  sentTime: z.string().optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
  tags: z.array(z.string()).default([]),
  metadata: z.record(z.any()).default({}),
});

/**
 * Type for creating a new campaign.
 */
export type CreateCampaignData = Omit<Campaign, 'id' | 'createdAt' | 'updatedAt' | 'metrics'> & { metrics?: Partial<CampaignMetrics> };

/**
 * Schema for creating a new campaign.
 */
export const createCampaignSchema = campaignSchema.omit({ 
  id: true, 
  createdAt: true, 
  updatedAt: true 
}).extend({
  metrics: campaignMetricsSchema.partial().default({}),
});