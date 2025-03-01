import React from 'react';
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';
import CanvasLayout from '@/components/Canvas/CanvasLayout';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import ThoughtVisualizer from '@/components/Canvas/ThoughtVisualizer';
import AIChatContainer from './AIChatContainer';

async function getCanvasName(canvasId: string): Promise<string> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/canvas/${canvasId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      return 'Canvas';
    }

    const data = await response.json();
    return data.name || 'Canvas';
  } catch (error) {
    console.error('Error fetching canvas name:', error);
    return 'Canvas';
  }
}

export default async function CanvasAIAssistantPage({ params }: { params: { id: string } }) {
  const canvasId = params.id;
  const session = await getSession();

  if (!session?.user) {
    redirect('/login?callbackUrl=/canvas/' + canvasId + '/ai-assistant');
  }

  const canvasName = await getCanvasName(canvasId);

  return (
    <CanvasLayout
      title={`${canvasName} - AI Assistant`}
      description="Get help from the AI assistant with your canvas"
      showBackButton
      backButtonUrl={`/canvas/${canvasId}`}
      backButtonText="Back to Canvas"
      activeNavItem="ai-assistant"
    >
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* AI Chat Section */}
        <div className="lg:col-span-2">
          <AIChatContainer canvasId={canvasId} />
        </div>

        {/* Thought Visualization */}
        <div className="lg:col-span-3">
          <ThoughtVisualizer
            canvasId={canvasId}
            height="700px"
          />
        </div>
      </div>
    </CanvasLayout>
  );
}
