/**
 * AI Integration Service
 * 
 * This service integrates the Email Service with the AI Mesh Network for content optimization,
 * AI-driven template selection, sentiment analysis, and A/B testing capabilities.
 */

import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../utils/logger';
import { retry } from '../utils/retry';
import { prisma } from '../lib/prisma';
import { Template } from '../models/template';
import { Email } from '../models/email';
import { Campaign } from '../models/campaign';
import { ABTest, ABTestVariant, ABTestStatus } from '../models/ab-test';
import { SentimentAnalysisResult, SentimentScore } from '../models/sentiment';

// Environment variables
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://ai-service:8001';
const AI_MESH_URL = process.env.AI_MESH_URL || 'http://ai-mesh:8005';
const API_KEY = process.env.INTERNAL_API_KEY || '';
const ENABLE_SENTIMENT_ANALYSIS = process.env.ENABLE_SENTIMENT_ANALYSIS === 'true';
const ENABLE_AB_TESTING = process.env.ENABLE_AB_TESTING === 'true';
const ENABLE_TEMPLATE_SELECTION = process.env.ENABLE_TEMPLATE_SELECTION === 'true';
const ENABLE_CONTENT_OPTIMIZATION = process.env.ENABLE_CONTENT_OPTIMIZATION === 'true';

/**
 * AI Integration Service
 */
export class AIIntegrationService {
  /**
   * Generate email content using AI
   * 
   * @param prompt Prompt for content generation
   * @param context Context for content generation
   * @param options Generation options
   * @returns Generated content
   */
  async generateContent(
    prompt: string,
    context: Record<string, any>,
    options: {
      maxLength?: number;
      temperature?: number;
      style?: string;
      tone?: string;
      format?: string;
    } = {}
  ): Promise<string> {
    try {
      logger.info('Generating email content using AI');
      
      const response = await retry(
        () =>
          axios.post(
            `${AI_SERVICE_URL}/generate`,
            {
              prompt,
              context,
              options: {
                maxLength: options.maxLength || 1000,
                temperature: options.temperature || 0.7,
                style: options.style || 'professional',
                tone: options.tone || 'friendly',
                format: options.format || 'html',
              },
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for content generation: ${error.message}`);
          },
        }
      );
      
      return response.data.content;
    } catch (error) {
      logger.error('Error generating email content:', error);
      throw new Error('Failed to generate email content');
    }
  }
  
  /**
   * Optimize email content using AI
   * 
   * @param content Original content
   * @param options Optimization options
   * @returns Optimized content
   */
  async optimizeContent(
    content: string,
    options: {
      goal?: 'engagement' | 'conversion' | 'retention' | 'information';
      audience?: string;
      constraints?: string[];
      format?: string;
    } = {}
  ): Promise<string> {
    if (!ENABLE_CONTENT_OPTIMIZATION) {
      logger.info('Content optimization is disabled');
      return content;
    }
    
    try {
      logger.info('Optimizing email content using AI');
      
      const response = await retry(
        () =>
          axios.post(
            `${AI_MESH_URL}/optimize`,
            {
              content,
              options: {
                goal: options.goal || 'engagement',
                audience: options.audience || 'general',
                constraints: options.constraints || [],
                format: options.format || 'html',
              },
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for content optimization: ${error.message}`);
          },
        }
      );
      
      return response.data.optimizedContent;
    } catch (error) {
      logger.error('Error optimizing email content:', error);
      // Return original content if optimization fails
      return content;
    }
  }
  
  /**
   * Analyze sentiment of email content
   * 
   * @param content Email content
   * @returns Sentiment analysis result
   */
  async analyzeSentiment(content: string): Promise<SentimentAnalysisResult> {
    if (!ENABLE_SENTIMENT_ANALYSIS) {
      logger.info('Sentiment analysis is disabled');
      return {
        score: SentimentScore.NEUTRAL,
        confidence: 1.0,
        details: {
          positive: 0.5,
          negative: 0.5,
          neutral: 0.5,
        },
      };
    }
    
    try {
      logger.info('Analyzing sentiment of email content');
      
      const response = await retry(
        () =>
          axios.post(
            `${AI_SERVICE_URL}/analyze/sentiment`,
            {
              content,
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for sentiment analysis: ${error.message}`);
          },
        }
      );
      
      return response.data;
    } catch (error) {
      logger.error('Error analyzing sentiment:', error);
      throw new Error('Failed to analyze sentiment');
    }
  }
  
  /**
   * Select the best template for a campaign using AI
   * 
   * @param campaign Campaign
   * @param templates Available templates
   * @param options Selection options
   * @returns Selected template
   */
  async selectTemplate(
    campaign: Campaign,
    templates: Template[],
    options: {
      audience?: string;
      goal?: string;
      industry?: string;
    } = {}
  ): Promise<Template> {
    if (!ENABLE_TEMPLATE_SELECTION || templates.length === 0) {
      logger.info('Template selection is disabled or no templates available');
      return templates[0];
    }
    
    try {
      logger.info(`Selecting best template for campaign ${campaign.id}`);
      
      const response = await retry(
        () =>
          axios.post(
            `${AI_MESH_URL}/select-template`,
            {
              campaign: {
                id: campaign.id,
                name: campaign.name,
                subject: campaign.subject,
                description: campaign.description,
                metadata: campaign.metadata,
              },
              templates: templates.map(template => ({
                id: template.id,
                name: template.name,
                content: template.content,
                metadata: template.metadata,
              })),
              options: {
                audience: options.audience || campaign.metadata?.audience || 'general',
                goal: options.goal || campaign.metadata?.goal || 'engagement',
                industry: options.industry || campaign.metadata?.industry || 'general',
              },
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for template selection: ${error.message}`);
          },
        }
      );
      
      const selectedTemplateId = response.data.selectedTemplateId;
      const selectedTemplate = templates.find(template => template.id === selectedTemplateId);
      
      if (!selectedTemplate) {
        logger.warn(`Selected template ${selectedTemplateId} not found in provided templates`);
        return templates[0];
      }
      
      return selectedTemplate;
    } catch (error) {
      logger.error('Error selecting template:', error);
      // Return first template if selection fails
      return templates[0];
    }
  }
  
  /**
   * Create A/B test variants for a campaign
   * 
   * @param campaign Campaign
   * @param baseContent Base content
   * @param options A/B test options
   * @returns A/B test with variants
   */
  async createABTest(
    campaign: Campaign,
    baseContent: string,
    options: {
      variantCount?: number;
      testType?: 'subject' | 'content' | 'both';
      testGoal?: 'opens' | 'clicks' | 'conversions';
      audiencePercentage?: number;
    } = {}
  ): Promise<ABTest> {
    if (!ENABLE_AB_TESTING) {
      logger.info('A/B testing is disabled');
      throw new Error('A/B testing is disabled');
    }
    
    try {
      logger.info(`Creating A/B test for campaign ${campaign.id}`);
      
      const variantCount = options.variantCount || 2;
      const testType = options.testType || 'both';
      const testGoal = options.testGoal || 'clicks';
      const audiencePercentage = options.audiencePercentage || 100;
      
      // Create A/B test in database
      const abTest = await prisma.abTest.create({
        data: {
          id: uuidv4(),
          campaignId: campaign.id,
          status: ABTestStatus.CREATED,
          testType,
          testGoal,
          audiencePercentage,
          startedAt: new Date(),
        },
      });
      
      // Generate variants
      const variants: ABTestVariant[] = [];
      
      // Add control variant
      variants.push({
        id: uuidv4(),
        abTestId: abTest.id,
        name: 'Control',
        subject: campaign.subject,
        content: baseContent,
        isControl: true,
      });
      
      // Generate additional variants
      const response = await retry(
        () =>
          axios.post(
            `${AI_MESH_URL}/generate-variants`,
            {
              campaign: {
                id: campaign.id,
                name: campaign.name,
                subject: campaign.subject,
                description: campaign.description,
                metadata: campaign.metadata,
              },
              baseContent,
              options: {
                variantCount: variantCount - 1, // Subtract control variant
                testType,
                testGoal,
              },
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for variant generation: ${error.message}`);
          },
        }
      );
      
      // Add generated variants
      for (const variant of response.data.variants) {
        variants.push({
          id: uuidv4(),
          abTestId: abTest.id,
          name: variant.name,
          subject: variant.subject || campaign.subject,
          content: variant.content,
          isControl: false,
        });
      }
      
      // Store variants in database
      await prisma.abTestVariant.createMany({
        data: variants.map(variant => ({
          id: variant.id,
          abTestId: variant.abTestId,
          name: variant.name,
          subject: variant.subject,
          content: variant.content,
          isControl: variant.isControl,
        })),
      });
      
      // Update A/B test status
      await prisma.abTest.update({
        where: { id: abTest.id },
        data: {
          status: ABTestStatus.READY,
          variantCount: variants.length,
        },
      });
      
      return {
        ...abTest,
        variants,
        variantCount: variants.length,
        status: ABTestStatus.READY,
      };
    } catch (error) {
      logger.error('Error creating A/B test:', error);
      throw new Error('Failed to create A/B test');
    }
  }
  
  /**
   * Evaluate A/B test results
   * 
   * @param abTestId A/B test ID
   * @returns Evaluation results
   */
  async evaluateABTest(abTestId: string): Promise<{
    winnerId: string;
    confidence: number;
    results: Record<string, any>;
  }> {
    try {
      logger.info(`Evaluating A/B test ${abTestId}`);
      
      // Get A/B test with variants and metrics
      const abTest = await prisma.abTest.findUnique({
        where: { id: abTestId },
        include: {
          variants: {
            include: {
              metrics: true,
            },
          },
        },
      });
      
      if (!abTest) {
        throw new Error(`A/B test ${abTestId} not found`);
      }
      
      // Check if A/B test is completed
      if (abTest.status !== ABTestStatus.COMPLETED) {
        throw new Error(`A/B test ${abTestId} is not completed`);
      }
      
      // Evaluate results using AI
      const response = await retry(
        () =>
          axios.post(
            `${AI_MESH_URL}/evaluate-ab-test`,
            {
              abTest: {
                id: abTest.id,
                testType: abTest.testType,
                testGoal: abTest.testGoal,
                variants: abTest.variants.map(variant => ({
                  id: variant.id,
                  name: variant.name,
                  isControl: variant.isControl,
                  metrics: variant.metrics,
                })),
              },
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for A/B test evaluation: ${error.message}`);
          },
        }
      );
      
      const evaluation = response.data;
      
      // Update A/B test with winner
      await prisma.abTest.update({
        where: { id: abTest.id },
        data: {
          winnerId: evaluation.winnerId,
          winnerConfidence: evaluation.confidence,
          results: evaluation.results,
          completedAt: new Date(),
        },
      });
      
      return evaluation;
    } catch (error) {
      logger.error(`Error evaluating A/B test ${abTestId}:`, error);
      throw new Error('Failed to evaluate A/B test');
    }
  }
  
  /**
   * Get personalized content recommendations for a recipient
   * 
   * @param email Email
   * @param recipient Recipient
   * @returns Personalized content recommendations
   */
  async getPersonalizedRecommendations(
    email: Email,
    recipient: {
      email: string;
      name?: string;
      metadata?: Record<string, any>;
    }
  ): Promise<{
    subject?: string;
    content?: string;
    recommendations: Array<{
      type: string;
      content: string;
      confidence: number;
    }>;
  }> {
    try {
      logger.info(`Getting personalized recommendations for ${recipient.email}`);
      
      const response = await retry(
        () =>
          axios.post(
            `${AI_MESH_URL}/personalize`,
            {
              email: {
                id: email.id,
                subject: email.subject,
                content: email.content,
                metadata: email.metadata,
              },
              recipient: {
                email: recipient.email,
                name: recipient.name,
                metadata: recipient.metadata,
              },
            },
            {
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
          onRetry: (error, attempt) => {
            logger.warn(`Retry ${attempt} for personalized recommendations: ${error.message}`);
          },
        }
      );
      
      return response.data;
    } catch (error) {
      logger.error(`Error getting personalized recommendations for ${recipient.email}:`, error);
      
      // Return empty recommendations if personalization fails
      return {
        recommendations: [],
      };
    }
  }
}

// Export singleton instance
export const aiIntegrationService = new AIIntegrationService();
