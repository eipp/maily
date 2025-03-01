/**
 * OpenAI Model Adapter Implementation
 *
 * This adapter provides implementations for the ModelAdapter interface
 * using OpenAI's GPT models via their API.
 */
import OpenAI from 'openai';
import {
  ModelAdapter,
  ModelConfig,
  Message,
  CompletionResponse,
  modelAdapterFactory
} from './model-adapter';

// OpenAI-specific configuration
export interface OpenAIConfig extends ModelConfig {
  model?: string;
  apiKey?: string;
  organization?: string;
}

// Default prompt templates
const PROMPT_TEMPLATES = {
  emailSubject: `Generate a compelling email subject line based on the following email content.
The subject should be attention-grabbing, clear, and encourage opens.
Email content: {{emailContent}}
Target audience: {{audience}}
Desired tone: {{tone}}
Respond with ONLY the subject line, nothing else.`,

  optimizeEmail: `Optimize the following email content for better engagement.
Focus on clarity, conciseness, and persuasiveness.
Target metrics to optimize for: {{targetMetrics}}
Original email content: {{emailContent}}
Respond with ONLY the optimized email content, maintaining the original HTML formatting if present.`,

  generateEmail: `Generate email content for a marketing campaign with the following parameters:
Topic: {{topic}}
Target audience: {{audience}}
Tone: {{tone}}
Length: {{length}}
Create compelling content that resonates with the audience and drives engagement.`,

  subjectVariations: `Generate {{count}} different subject line variations for the following email content.
Each variation should be unique in approach but maintain the core message.
Email content: {{emailContent}}
Respond with ONLY the numbered list of subject lines, one per line.`
};

/**
 * OpenAI Model Adapter
 *
 * Adapter for OpenAI GPT models
 */
export class OpenAIAdapter extends ModelAdapter {
  private client: OpenAI;
  private openaiConfig: OpenAIConfig;

  constructor(config?: OpenAIConfig) {
    super(config);
    this.openaiConfig = {
      model: 'gpt-4',
      ...config
    };

    // Initialize OpenAI client
    this.client = new OpenAI({
      apiKey: this.openaiConfig.apiKey || process.env.OPENAI_API_KEY,
      organization: this.openaiConfig.organization || process.env.OPENAI_ORGANIZATION,
    });
  }

  /**
   * Generate text based on a prompt
   */
  async generateText(prompt: string): Promise<CompletionResponse> {
    try {
      const completion = await this.client.chat.completions.create({
        model: this.openaiConfig.model || 'gpt-4',
        messages: [{ role: 'user', content: prompt }],
        temperature: this.config.temperature,
        max_tokens: this.config.maxTokens,
        top_p: this.config.topP,
        frequency_penalty: this.config.frequencyPenalty,
        presence_penalty: this.config.presencePenalty,
      });

      return {
        content: completion.choices[0]?.message?.content || '',
        usage: {
          promptTokens: completion.usage?.prompt_tokens || 0,
          completionTokens: completion.usage?.completion_tokens || 0,
          totalTokens: completion.usage?.total_tokens || 0,
        }
      };
    } catch (error) {
      console.error('OpenAI API error:', error);
      throw new Error(`Failed to generate text: ${error.message}`);
    }
  }

  /**
   * Generate chat completion based on a series of messages
   */
  async generateChatCompletion(messages: Message[]): Promise<CompletionResponse> {
    try {
      // Map our message format to OpenAI's format
      const openaiMessages = messages.map(message => ({
        role: message.role,
        content: message.content,
      }));

      const completion = await this.client.chat.completions.create({
        model: this.openaiConfig.model || 'gpt-4',
        messages: openaiMessages,
        temperature: this.config.temperature,
        max_tokens: this.config.maxTokens,
        top_p: this.config.topP,
        frequency_penalty: this.config.frequencyPenalty,
        presence_penalty: this.config.presencePenalty,
      });

      return {
        content: completion.choices[0]?.message?.content || '',
        usage: {
          promptTokens: completion.usage?.prompt_tokens || 0,
          completionTokens: completion.usage?.completion_tokens || 0,
          totalTokens: completion.usage?.total_tokens || 0,
        }
      };
    } catch (error) {
      console.error('OpenAI API error:', error);
      throw new Error(`Failed to generate chat completion: ${error.message}`);
    }
  }

  /**
   * Generate email subject line based on email content
   */
  async generateEmailSubject(
    emailContent: string,
    audience: string = 'general',
    tone: string = 'professional'
  ): Promise<string> {
    const prompt = PROMPT_TEMPLATES.emailSubject
      .replace('{{emailContent}}', emailContent)
      .replace('{{audience}}', audience)
      .replace('{{tone}}', tone);

    const response = await this.generateText(prompt);
    return response.content.trim();
  }

  /**
   * Optimize email content for better engagement
   */
  async optimizeEmailContent(
    emailContent: string,
    targetMetrics: string[] = ['open rate', 'click-through rate']
  ): Promise<string> {
    const prompt = PROMPT_TEMPLATES.optimizeEmail
      .replace('{{emailContent}}', emailContent)
      .replace('{{targetMetrics}}', targetMetrics.join(', '));

    const response = await this.generateText(prompt);
    return response.content.trim();
  }

  /**
   * Generate email content suggestions
   */
  async generateEmailContent(
    topic: string,
    audience: string = 'general',
    tone: string = 'professional',
    length: 'short' | 'medium' | 'long' = 'medium'
  ): Promise<string> {
    const prompt = PROMPT_TEMPLATES.generateEmail
      .replace('{{topic}}', topic)
      .replace('{{audience}}', audience)
      .replace('{{tone}}', tone)
      .replace('{{length}}', length);

    const response = await this.generateText(prompt);
    return response.content.trim();
  }

  /**
   * A/B test subject lines
   */
  async generateSubjectLineVariations(
    emailContent: string,
    count: number = 3
  ): Promise<string[]> {
    const prompt = PROMPT_TEMPLATES.subjectVariations
      .replace('{{emailContent}}', emailContent)
      .replace('{{count}}', count.toString());

    const response = await this.generateText(prompt);

    // Parse the numbered list response into an array of subject lines
    const subjectLines = response.content
      .split('\n')
      .filter(line => line.trim() !== '')
      .map(line => {
        // Remove numbers, periods, and leading/trailing whitespace
        return line.replace(/^\d+\.?\s*/, '').trim();
      });

    return subjectLines.slice(0, count);
  }

  /**
   * Set OpenAI-specific configuration
   */
  setOpenAIConfig(config: Partial<OpenAIConfig>): void {
    this.openaiConfig = { ...this.openaiConfig, ...config };

    // Reinitialize client if API key or organization changes
    if (config.apiKey || config.organization) {
      this.client = new OpenAI({
        apiKey: this.openaiConfig.apiKey || process.env.OPENAI_API_KEY,
        organization: this.openaiConfig.organization || process.env.OPENAI_ORGANIZATION,
      });
    }
  }
}

// Register the OpenAI adapter with the factory
modelAdapterFactory.registerAdapter('openai', OpenAIAdapter);
