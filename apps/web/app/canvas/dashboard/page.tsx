'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Edit, Plus, Share2, Trash2 } from 'lucide-react';
import Link from 'next/link';
import CanvasLayout from '@/components/Canvas/CanvasLayout';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';

interface Canvas {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  owner_id: string;
  collaborator_count: number;
}

async function getCanvases() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/canvas`, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error('Failed to fetch canvases');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching canvases:', error);
    return { canvases: [] };
  }
}

export default async function CanvasDashboardPage() {
  const session = await getSession();

  if (!session?.user) {
    redirect('/login?callbackUrl=/canvas/dashboard');
  }

  const { canvases = [] } = await getCanvases();

  return (
    <CanvasLayout
      title="Your Canvases"
      description="Manage and create new collaborative canvases"
      showBackButton
      backButtonUrl="/dashboard"
      backButtonText="Back to Main Dashboard"
      activeNavItem="dashboard"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Create New Canvas Card */}
        <Card className="border-dashed border-2 hover:border-primary/50 transition-colors">
          <CardHeader className="text-center">
            <CardTitle>Create New Canvas</CardTitle>
            <CardDescription>Start a new collaborative canvas</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center items-center pb-6">
            <Button asChild>
              <Link href="/canvas/new" className="flex items-center">
                <Plus className="mr-2 h-4 w-4" />
                New Canvas
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Existing Canvases */}
        {canvases.length > 0 ? (
          canvases.map((canvas: any) => (
            <Card key={canvas.id}>
              <CardHeader>
                <CardTitle>{canvas.name}</CardTitle>
                <CardDescription>
                  Created: {new Date(canvas.created_at).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {canvas.description || 'No description provided'}
                </p>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button asChild variant="default">
                  <Link href={`/canvas/${canvas.id}`}>Open Canvas</Link>
                </Button>
                <div className="flex space-x-2">
                  <Button size="icon" variant="outline">
                    <Share2 className="h-4 w-4" />
                  </Button>
                  <Button size="icon" variant="outline" className="text-destructive">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))
        ) : (
          <Card className="col-span-full">
            <CardHeader>
              <CardTitle>No Canvases Found</CardTitle>
              <CardDescription>You haven't created any canvases yet.</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Get started by creating your first canvas!</p>
            </CardContent>
          </Card>
        )}
      </div>
    </CanvasLayout>
  );
}
