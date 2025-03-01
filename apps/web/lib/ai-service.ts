import { db } from '@/lib/db';
import { decrypt } from '@/lib/encryption';

// Default API keys from environment variables
const DEFAULT_OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const DEFAULT_ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;

// List of models that don't require a user-provided API key
const DEFAULT_MODELS = ['default-model-1', 'default-model-2'];

interface AIModelRequest {
  prompt: string;
  userId?: string;
  agentId: string;
  options?: Record<string, any>;
}

interface AIModelResponse {
  text: string;
  modelUsed: string;
  tokenUsage?: {
    prompt: number;
    completion: number;
    total: number;
  };
}

/**
 * Get the appropriate API key for a model
 * @param userId The user ID
 * @param agentId The agent ID
 * @returns The API key and model ID to use
 */
export async function getModelConfig(userId: string, agentId: string): Promise<{ modelId: string; apiKey: string | null }> {
  try {
    // Get the user's model setting for this agent
    const setting = await db.userModelSettings.findUnique({
      where: {
        userId_agentId: {
          userId,
          agentId,
        },
      },
    });

    // If no setting is found, use the default model
    if (!setting) {
      return {
        modelId: 'default-model-1',
        apiKey: null,
      };
    }

    // If the model is a default model, no API key is needed
    if (DEFAULT_MODELS.includes(setting.modelId)) {
      return {
        modelId: setting.modelId,
        apiKey: null,
      };
    }

    // For BYOK models, decrypt the API key
    let apiKey = null;
    if (setting.apiKey) {
      apiKey = await decrypt(setting.apiKey);
    }

    return {
      modelId: setting.modelId,
      apiKey,
    };
  } catch (error) {
    console.error('Error getting model config:', error);
    // Fall back to default model
    return {
      modelId: 'default-model-1',
      apiKey: null,
    };
  }
}

/**
 * Call an AI model with the appropriate API key
 * @param request The request parameters
 * @returns The AI model response
 */
export async function callAIModel(request: AIModelRequest): Promise<AIModelResponse> {
  const { prompt, userId, agentId, options = {} } = request;

  try {
    // If no userId is provided, use the default model
    if (!userId) {
      return callDefaultModel(prompt, options);
    }

    // Get the model configuration for this user and agent
    const { modelId, apiKey } = await getModelConfig(userId, agentId);

    // Call the appropriate model provider
    if (modelId.startsWith('openai')) {
      return callOpenAIModel(prompt, modelId, apiKey || DEFAULT_OPENAI_API_KEY, options);
    } else if (modelId.startsWith('anthropic')) {
      return callAnthropicModel(prompt, modelId, apiKey || DEFAULT_ANTHROPIC_API_KEY, options);
    } else {
      // For default models, use our internal implementation
      return callDefaultModel(prompt, options);
    }
  } catch (error) {
    console.error('Error calling AI model:', error);
    throw new Error('Failed to call AI model');
  }
}

/**
 * Call OpenAI model
 */
async function callOpenAIModel(
  prompt: string,
  modelId: string,
  apiKey: string,
  options: Record<string, any>
): Promise<AIModelResponse> {
  try {
    // Map our model IDs to actual OpenAI model names
    const modelMap: Record<string, string> = {
      'openai-gpt4': 'gpt-4-turbo-preview',
      'openai-gpt35': 'gpt-3.5-turbo',
    };

    const modelName = modelMap[modelId] || 'gpt-3.5-turbo';

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: modelName,
        messages: [{ role: 'user', content: prompt }],
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 500,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`OpenAI API error: ${error.error?.message || 'Unknown error'}`);
    }

    const data = await response.json();

    return {
      text: data.choices[0].message.content,
      modelUsed: modelId,
      tokenUsage: {
        prompt: data.usage.prompt_tokens,
        completion: data.usage.completion_tokens,
        total: data.usage.total_tokens,
      },
    };
  } catch (error) {
    console.error('Error calling OpenAI model:', error);
    throw error;
  }
}

/**
 * Call Anthropic model
 */
async function callAnthropicModel(
  prompt: string,
  modelId: string,
  apiKey: string,
  options: Record<string, any>
): Promise<AIModelResponse> {
  try {
    // Map our model IDs to actual Anthropic model names
    const modelMap: Record<string, string> = {
      'anthropic-claude': 'claude-2',
      'anthropic-claude-instant': 'claude-instant-1',
    };

    const modelName = modelMap[modelId] || 'claude-2';

    const response = await fetch('https://api.anthropic.com/v1/complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: modelName,
        prompt: `\n\nHuman: ${prompt}\n\nAssistant:`,
        max_tokens_to_sample: options.maxTokens || 500,
        temperature: options.temperature || 0.7,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Anthropic API error: ${error.error?.message || 'Unknown error'}`);
    }

    const data = await response.json();

    return {
      text: data.completion,
      modelUsed: modelId,
      // Anthropic doesn't provide token usage in the same way
      tokenUsage: {
        prompt: 0,
        completion: 0,
        total: 0,
      },
    };
  } catch (error) {
    console.error('Error calling Anthropic model:', error);
    throw error;
  }
}

/**
 * Call default model (our own implementation)
 */
async function callDefaultModel(
  prompt: string,
  options: Record<string, any>
): Promise<AIModelResponse> {
  try {
    // In a real implementation, this would call your own model or a service
    // For demo purposes, we'll just return a simple response

    // Simulate a delay to mimic API call
    await new Promise(resolve => setTimeout(resolve, 500));

    return {
      text: `This is a response from the default model to your prompt: "${prompt}"`,
      modelUsed: 'default-model-1',
      tokenUsage: {
        prompt: prompt.split(' ').length,
        completion: 20,
        total: prompt.split(' ').length + 20,
      },
    };
  } catch (error) {
    console.error('Error calling default model:', error);
    throw error;
  }
}
