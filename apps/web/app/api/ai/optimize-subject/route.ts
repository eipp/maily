import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { callAIModel } from '@/lib/ai-service';

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
    const { subject, audience } = await req.json();

    if (!subject) {
      return NextResponse.json(
        { error: 'Subject line is required' },
        { status: 400 }
      );
    }

    // Create the prompt for the AI model
    const prompt = `
      You are an expert email marketer. Your task is to optimize the following email subject line
      to increase open rates for the specified audience.

      Original subject line: "${subject}"
      Target audience: ${audience || 'general'}

      Please provide 3 alternative subject lines that are more engaging, clear, and likely to drive higher open rates.
      Format your response as a JSON array of strings, with no additional text.
      Example: ["Alternative 1", "Alternative 2", "Alternative 3"]
    `;

    // Call the AI model using the user's selected model for subject optimization
    const response = await callAIModel({
      prompt,
      userId,
      agentId: 'subject-optimizer',
      options: {
        temperature: 0.7,
        maxTokens: 200,
      },
    });

    // Parse the response as JSON
    let alternatives;
    try {
      alternatives = JSON.parse(response.text);

      // Ensure the response is an array of strings
      if (!Array.isArray(alternatives) || alternatives.length === 0) {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Error parsing AI response:', error);

      // Fallback: extract alternatives from text if JSON parsing fails
      const lines = response.text.split('\n');
      alternatives = lines
        .filter(line => line.trim().startsWith('"') || line.trim().startsWith('- '))
        .map(line => line.replace(/^-\s*"|"$|^"|^-\s*/g, '').trim())
        .filter(line => line.length > 0);

      if (alternatives.length === 0) {
        alternatives = [
          `${subject} - Improved Version`,
          `Don't Miss: ${subject}`,
          `[Limited Time] ${subject}`,
        ];
      }
    }

    return NextResponse.json({
      originalSubject: subject,
      optimizedSubjects: alternatives.slice(0, 3),
      modelUsed: response.modelUsed,
      tokenUsage: response.tokenUsage,
    });
  } catch (error) {
    console.error('Error optimizing subject line:', error);
    return NextResponse.json(
      { error: 'Failed to optimize subject line' },
      { status: 500 }
    );
  }
}
