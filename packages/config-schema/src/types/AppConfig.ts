import { z } from 'zod';
import { DatabaseConfigSchema } from './DatabaseConfig';
import { RedisConfigSchema } from './RedisConfig';
import { AuthConfigSchema } from './AuthConfig';
import { LoggingConfigSchema } from './LoggingConfig';
import { EmailConfigSchema } from './EmailConfig';
import { AiConfigSchema } from './AiConfig';
import { ServiceConfigSchema } from './ServiceConfig';

/**
 * Application environment type
 */
export const EnvironmentSchema = z.enum([
  'development',
  'test',
  'staging',
  'production'
]);

export type Environment = z.infer<typeof EnvironmentSchema>;

/**
 * Feature flags configuration
 */
export const FeatureFlagsSchema = z.object({
  enableAiMeshNetwork: z.boolean().default(false),
  enableBlockchainVerification: z.boolean().default(false),
  enableAdvancedAnalytics: z.boolean().default(false),
  enableMultiPlatformIntegration: z.boolean().default(false),
  enableCanvasEditing: z.boolean().default(true),
  enableEmailVerification: z.boolean().default(true),
  enableCognitiveCanvas: z.boolean().default(false),
});

export type FeatureFlags = z.infer<typeof FeatureFlagsSchema>;

/**
 * Core application configuration
 */
export const AppConfigSchema = z.object({
  /**
   * Application environment
   */
  environment: EnvironmentSchema,
  
  /**
   * Application port
   */
  port: z.number().min(1).max(65535),
  
  /**
   * Application host
   */
  host: z.string().default('0.0.0.0'),
  
  /**
   * Base URL for the application
   */
  baseUrl: z.string().url(),
  
  /**
   * API endpoint URL
   */
  apiUrl: z.string().url(),
  
  /**
   * Web application URL
   */
  webUrl: z.string().url(),
  
  /**
   * Database configuration
   */
  database: DatabaseConfigSchema,
  
  /**
   * Redis configuration
   */
  redis: RedisConfigSchema,
  
  /**
   * Authentication configuration
   */
  auth: AuthConfigSchema,
  
  /**
   * Logging configuration
   */
  logging: LoggingConfigSchema,
  
  /**
   * Email sending configuration
   */
  email: EmailConfigSchema,
  
  /**
   * AI service configuration
   */
  ai: AiConfigSchema,
  
  /**
   * Service-specific configuration
   */
  services: ServiceConfigSchema,
  
  /**
   * Feature flags
   */
  featureFlags: FeatureFlagsSchema.default({}),
  
  /**
   * CORS allowed origins
   */
  corsAllowedOrigins: z.array(z.string()).default(['*']),
  
  /**
   * Rate limiting configuration
   */
  rateLimit: z.object({
    enabled: z.boolean().default(true),
    windowMs: z.number().default(60000), // 1 minute
    max: z.number().default(100), // 100 requests per minute
  }).default({}),
});

export type AppConfig = z.infer<typeof AppConfigSchema>;