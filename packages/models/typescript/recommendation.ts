/**
 * Recommendation models for the Maily platform.
 */
import { z } from 'zod';

/**
 * Recommendation type enumeration.
 */
export enum RecommendationType {
  THRESHOLD = 'threshold',
  TREND = 'trend',
  ANOMALY = 'anomaly',
  COMPARISON = 'comparison',
  AI_GENERATED = 'ai_generated',
}

/**
 * User actions on recommendations.
 */
export enum RecommendationAction {
  VIEW = 'view',
  CLICK = 'click',
  DISMISS = 'dismiss',
  APPLY = 'apply',
}

/**
 * Context data for a recommendation.
 */
export interface RecommendationContext {
  metric: string;
  value: number;
  confidence: number;
  threshold?: number;
  previousValue?: number;
  changePercent?: number;
  metadata: Record<string, any>;
}

/**
 * Recommendation model.
 */
export interface Recommendation {
  id: string;
  ruleId: string;
  ruleName: string;
  type: RecommendationType;
  message: string;
  suggestion: string;
  context: RecommendationContext;
  priority: number;
  tags: string[];
  entityType?: string;
  entityId?: string;
  userId?: string;
  timestamp: string;
  expiresAt?: string;
  dismissed: boolean;
  applied: boolean;
}

/**
 * Record of a user interaction with a recommendation.
 */
export interface RecommendationInteraction {
  id: string;
  recommendationId: string;
  userId: string;
  action: RecommendationAction;
  entityId?: string;
  entityType?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

/**
 * Recommendation context schema for validation.
 */
export const recommendationContextSchema = z.object({
  metric: z.string(),
  value: z.number(),
  confidence: z.number(),
  threshold: z.number().optional(),
  previousValue: z.number().optional(),
  changePercent: z.number().optional(),
  metadata: z.record(z.any()).default({}),
});

/**
 * Recommendation schema for validation.
 */
export const recommendationSchema = z.object({
  id: z.string(),
  ruleId: z.string(),
  ruleName: z.string(),
  type: z.nativeEnum(RecommendationType),
  message: z.string(),
  suggestion: z.string(),
  context: recommendationContextSchema,
  priority: z.number(),
  tags: z.array(z.string()).default([]),
  entityType: z.string().optional(),
  entityId: z.string().optional(),
  userId: z.string().optional(),
  timestamp: z.string(),
  expiresAt: z.string().optional(),
  dismissed: z.boolean().default(false),
  applied: z.boolean().default(false),
});

/**
 * Recommendation interaction schema for validation.
 */
export const recommendationInteractionSchema = z.object({
  id: z.string(),
  recommendationId: z.string(),
  userId: z.string(),
  action: z.nativeEnum(RecommendationAction),
  entityId: z.string().optional(),
  entityType: z.string().optional(),
  timestamp: z.string(),
  metadata: z.record(z.any()).default({}),
});

/**
 * Type for creating a new recommendation interaction.
 */
export type CreateRecommendationInteractionData = Omit<RecommendationInteraction, 'id' | 'timestamp'>;

/**
 * Schema for creating a new recommendation interaction.
 */
export const createRecommendationInteractionSchema = recommendationInteractionSchema.omit({
  id: true,
  timestamp: true,
});