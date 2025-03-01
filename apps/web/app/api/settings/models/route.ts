import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { db } from '@/lib/db';
import { encrypt, decrypt } from '@/lib/encryption';

export async function GET(req: NextRequest) {
  try {
    // Get the authenticated user
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.id;

    // Fetch user's model settings from the database
    const userSettings = await db.userModelSettings.findMany({
      where: { userId },
    });

    // Format the response
    const formattedSettings = userSettings.map(setting => ({
      agentId: setting.agentId,
      modelId: setting.modelId,
      // Don't send the actual API key to the frontend, just whether it exists
      hasApiKey: !!setting.apiKey,
    }));

    return NextResponse.json({ settings: formattedSettings });
  } catch (error) {
    console.error('Error fetching model settings:', error);
    return NextResponse.json(
      { error: 'Failed to fetch model settings' },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    // Get the authenticated user
    const session = await getServerSession(authOptions);

    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.id;
    const { agents } = await req.json();

    if (!agents || !Array.isArray(agents)) {
      return NextResponse.json(
        { error: 'Invalid request body' },
        { status: 400 }
      );
    }

    // Process each agent's settings
    const updatePromises = agents.map(async (agent) => {
      const { id: agentId, currentModelId, apiKey } = agent;

      // Find if this setting already exists
      const existingSetting = await db.userModelSettings.findFirst({
        where: {
          userId,
          agentId,
        },
      });

      // Encrypt API key if provided
      let encryptedApiKey = null;
      if (apiKey) {
        encryptedApiKey = await encrypt(apiKey);
      }

      if (existingSetting) {
        // Update existing setting
        return db.userModelSettings.update({
          where: {
            id: existingSetting.id,
          },
          data: {
            modelId: currentModelId,
            apiKey: encryptedApiKey,
            updatedAt: new Date(),
          },
        });
      } else {
        // Create new setting
        return db.userModelSettings.create({
          data: {
            userId,
            agentId,
            modelId: currentModelId,
            apiKey: encryptedApiKey,
          },
        });
      }
    });

    await Promise.all(updatePromises);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error saving model settings:', error);
    return NextResponse.json(
      { error: 'Failed to save model settings' },
      { status: 500 }
    );
  }
}

// Validate an API key with the provider
export async function PUT(req: NextRequest) {
  try {
    const { modelId, apiKey } = await req.json();

    if (!modelId || !apiKey) {
      return NextResponse.json(
        { error: 'Model ID and API key are required' },
        { status: 400 }
      );
    }

    let isValid = false;

    // Validate the API key with the appropriate provider
    if (modelId.startsWith('openai')) {
      isValid = await validateOpenAIKey(apiKey);
    } else if (modelId.startsWith('anthropic')) {
      isValid = await validateAnthropicKey(apiKey);
    } else {
      return NextResponse.json(
        { error: 'Unsupported model provider' },
        { status: 400 }
      );
    }

    return NextResponse.json({ isValid });
  } catch (error) {
    console.error('Error validating API key:', error);
    return NextResponse.json(
      { error: 'Failed to validate API key' },
      { status: 500 }
    );
  }
}

// Helper functions to validate API keys with providers
async function validateOpenAIKey(apiKey: string): Promise<boolean> {
  try {
    const response = await fetch('https://api.openai.com/v1/models', {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
      },
    });

    return response.status === 200;
  } catch (error) {
    console.error('Error validating OpenAI key:', error);
    return false;
  }
}

async function validateAnthropicKey(apiKey: string): Promise<boolean> {
  try {
    const response = await fetch('https://api.anthropic.com/v1/models', {
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
    });

    return response.status === 200;
  } catch (error) {
    console.error('Error validating Anthropic key:', error);
    return false;
  }
}
