/**
 * Model Adapter Interface for AI Capabilities
 *
 * This module defines interfaces and abstract classes for interacting with
 * different AI model providers through a unified interface.
 */

// Common interfaces

/**
 * Message structure for chat-based AI models
 */
export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

/**
 * Base configuration for AI models
 */
export interface ModelConfig {
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

/**
 * Response format for text generation
 */
export interface CompletionResponse {
  content: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

/**
 * Abstract Model Adapter
 *
 * Base class for all AI model adapters
 */
export abstract class ModelAdapter {
  protected config: ModelConfig;

  constructor(config: ModelConfig = {}) {
    this.config = {
      temperature: 0.7,
      maxTokens: 500,
      topP: 1,
      frequencyPenalty: 0,
      presencePenalty: 0,
      ...config,
    };
  }

  /**
   * Generate text based on a prompt
   * @param prompt The text prompt
   * @returns Generated completion
   */
  abstract generateText(prompt: string): Promise<CompletionResponse>;

  /**
   * Generate chat completion based on a series of messages
   * @param messages Array of messages
   * @returns Generated completion
   */
  abstract generateChatCompletion(messages: Message[]): Promise<CompletionResponse>;

  /**
   * Generate email subject line based on email content
   * @param emailContent Email body content
   * @param audience Target audience description
   * @param tone Desired tone (professional, friendly, etc.)
   * @returns Generated subject line
   */
  abstract generateEmailSubject(
    emailContent: string,
    audience?: string,
    tone?: string
  ): Promise<string>;

  /**
   * Optimize email content for better engagement
   * @param emailContent Original email content
   * @param targetMetrics Metrics to optimize for (open rate, click rate, etc.)
   * @returns Optimized email content
   */
  abstract optimizeEmailContent(
    emailContent: string,
    targetMetrics?: string[]
  ): Promise<string>;

  /**
   * Generate email content suggestions
   * @param topic Email topic
   * @param audience Target audience
   * @param tone Desired tone
   * @param length Approximate length (short, medium, long)
   * @returns Generated email content
   */
  abstract generateEmailContent(
    topic: string,
    audience?: string,
    tone?: string,
    length?: 'short' | 'medium' | 'long'
  ): Promise<string>;

  /**
   * A/B test subject lines
   * @param emailContent Email content
   * @param count Number of variations to generate
   * @returns Array of subject line variations
   */
  abstract generateSubjectLineVariations(
    emailContent: string,
    count?: number
  ): Promise<string[]>;

  /**
   * Set configuration for the model
   * @param config Configuration options
   */
  setConfig(config: Partial<ModelConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

/**
 * Model Adapter Factory
 *
 * Factory for creating model adapters
 */
export class ModelAdapterFactory {
  private static instance: ModelAdapterFactory;
  private adapters: Map<string, new (config?: ModelConfig) => ModelAdapter> = new Map();

  private constructor() {}

  public static getInstance(): ModelAdapterFactory {
    if (!ModelAdapterFactory.instance) {
      ModelAdapterFactory.instance = new ModelAdapterFactory();
    }
    return ModelAdapterFactory.instance;
  }

  /**
   * Register a model adapter
   * @param name Name of the adapter
   * @param adapterClass Adapter class
   */
  registerAdapter(name: string, adapterClass: new (config?: ModelConfig) => ModelAdapter): void {
    this.adapters.set(name, adapterClass);
  }

  /**
   * Create an instance of a model adapter
   * @param name Name of the adapter
   * @param config Configuration for the adapter
   * @returns Model adapter instance
   */
  createAdapter(name: string, config?: ModelConfig): ModelAdapter {
    const AdapterClass = this.adapters.get(name);
    if (!AdapterClass) {
      throw new Error(`Model adapter '${name}' not found`);
    }
    return new AdapterClass(config);
  }

  /**
   * Get available adapters
   * @returns List of registered adapter names
   */
  getAvailableAdapters(): string[] {
    return Array.from(this.adapters.keys());
  }
}

// Export singleton factory instance
export const modelAdapterFactory = ModelAdapterFactory.getInstance();
