/**
 * AI Service for Maily
 *
 * This service provides AI capabilities for the application by using
 * the model adapter to interact with AI models.
 */
import { modelAdapterFactory } from './model-adapter';
import { OpenAIAdapter } from './openai-adapter';

// Default adapter name
const DEFAULT_ADAPTER = 'openai';

// AI service class
class AIService {
  private static instance: AIService;
  private currentAdapter: string = DEFAULT_ADAPTER;

  private constructor() {
    // Ensure OpenAI adapter is registered
    if (!modelAdapterFactory.getAvailableAdapters().includes(DEFAULT_ADAPTER)) {
      modelAdapterFactory.registerAdapter('openai', OpenAIAdapter);
    }
  }

  /**
   * Get the singleton instance
   */
  public static getInstance(): AIService {
    if (!AIService.instance) {
      AIService.instance = new AIService();
    }
    return AIService.instance;
  }

  /**
   * Switch the active model adapter
   * @param adapterName Name of the adapter to use
   */
  setAdapter(adapterName: string): void {
    const availableAdapters = modelAdapterFactory.getAvailableAdapters();
    if (!availableAdapters.includes(adapterName)) {
      throw new Error(`Adapter '${adapterName}' not available. Available adapters: ${availableAdapters.join(', ')}`);
    }
    this.currentAdapter = adapterName;
  }

  /**
   * Get the current adapter name
   */
  getAdapterName(): string {
    return this.currentAdapter;
  }

  /**
   * Generate an email subject line based on content
   * @param emailContent Email body content
   * @param audience Target audience description
   * @param tone Desired tone
   * @returns Generated subject line
   */
  async generateEmailSubject(
    emailContent: string,
    audience?: string,
    tone?: string
  ): Promise<string> {
    try {
      const adapter = modelAdapterFactory.createAdapter(this.currentAdapter);
      return await adapter.generateEmailSubject(emailContent, audience, tone);
    } catch (error) {
      console.error('Failed to generate email subject:', error);
      throw error;
    }
  }

  /**
   * Generate multiple subject line variations for A/B testing
   * @param emailContent Email content
   * @param count Number of variations to generate
   * @returns Array of subject lines
   */
  async generateSubjectVariations(
    emailContent: string,
    count: number = 3
  ): Promise<string[]> {
    try {
      const adapter = modelAdapterFactory.createAdapter(this.currentAdapter);
      return await adapter.generateSubjectLineVariations(emailContent, count);
    } catch (error) {
      console.error('Failed to generate subject variations:', error);
      throw error;
    }
  }

  /**
   * Optimize email content for better engagement
   * @param emailContent Original email content
   * @param targetMetrics Metrics to optimize for
   * @returns Optimized content
   */
  async optimizeEmailContent(
    emailContent: string,
    targetMetrics?: string[]
  ): Promise<string> {
    try {
      const adapter = modelAdapterFactory.createAdapter(this.currentAdapter);
      return await adapter.optimizeEmailContent(emailContent, targetMetrics);
    } catch (error) {
      console.error('Failed to optimize email content:', error);
      throw error;
    }
  }

  /**
   * Generate email content based on parameters
   * @param topic Email topic
   * @param audience Target audience
   * @param tone Desired tone
   * @param length Content length
   * @returns Generated email content
   */
  async generateEmailContent(
    topic: string,
    audience?: string,
    tone?: string,
    length?: 'short' | 'medium' | 'long'
  ): Promise<string> {
    try {
      const adapter = modelAdapterFactory.createAdapter(this.currentAdapter);
      return await adapter.generateEmailContent(topic, audience, tone, length);
    } catch (error) {
      console.error('Failed to generate email content:', error);
      throw error;
    }
  }

  /**
   * Analyze campaign performance and provide insights
   * @param campaignData Campaign performance data
   * @returns Analysis and recommendations
   */
  async analyzeCampaignPerformance(campaignData: any): Promise<string> {
    try {
      const adapter = modelAdapterFactory.createAdapter(this.currentAdapter);
      const prompt = `Analyze the following email campaign performance data and provide insights and recommendations:
      ${JSON.stringify(campaignData, null, 2)}

      Please include:
      1. Key performance indicators analysis
      2. Comparison to industry benchmarks
      3. Actionable recommendations for improvement
      4. Specific suggestions for future campaigns`;

      const response = await adapter.generateText(prompt);
      return response.content;
    } catch (error) {
      console.error('Failed to analyze campaign performance:', error);
      throw error;
    }
  }

  /**
   * Suggest audience segments based on subscriber data
   * @param subscriberData Subscriber data
   * @returns Suggested segments with rationale
   */
  async suggestAudienceSegments(subscriberData: any): Promise<any> {
    try {
      const adapter = modelAdapterFactory.createAdapter(this.currentAdapter);
      const prompt = `Analyze the following subscriber data and suggest optimal audience segments:
      ${JSON.stringify(subscriberData, null, 2)}

      For each suggested segment, please provide:
      1. Segment name
      2. Description
      3. Targeting criteria
      4. Estimated size (percentage of total)
      5. Recommended content approach

      Return the segments as a properly formatted JSON array.`;

      const response = await adapter.generateText(prompt);
      try {
        return JSON.parse(response.content);
      } catch (parseError) {
        console.error('Failed to parse segment suggestions:', parseError);
        return response.content; // Return as text if parsing fails
      }
    } catch (error) {
      console.error('Failed to suggest audience segments:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const aiService = AIService.getInstance();
export default aiService;
