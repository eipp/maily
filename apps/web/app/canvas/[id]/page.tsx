'use client';

import { useEffect, useState } from 'react';
import { useParams, redirect } from 'next/navigation';
import CollaborativeCanvas from '@/components/Canvas/CollaborativeCanvas';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import CanvasLayout from '@/components/Canvas/CanvasLayout';
import { getSession } from '@/lib/auth';

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

export default async function CanvasPage({ params }: { params: { id: string } }) {
  const canvasId = params.id;
  const session = await getSession();

  if (!session?.user) {
    redirect('/login?callbackUrl=/canvas/' + canvasId);
  }

  const canvasName = await getCanvasName(canvasId);

  return (
    <CanvasLayout
      title={canvasName}
      description="Collaborate in real-time with your team"
      showBackButton
      backButtonUrl="/canvas/dashboard"
      backButtonText="Back to Canvas Dashboard"
      activeNavItem="canvas"
      maxWidth="full"
      canvasId={canvasId}
    >
      <CollaborativeCanvas canvasId={canvasId} userId={session.user.id} />
    </CanvasLayout>
  );
}
