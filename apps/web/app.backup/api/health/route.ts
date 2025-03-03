import { NextResponse } from 'next/server';

/**
 * Health check endpoint for Kubernetes probes
 *
 * This endpoint is used by Kubernetes to check if the application is healthy.
 * It returns a 200 OK response if the application is running properly.
 */
export async function GET() {
  return NextResponse.json(
    {
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: process.env.NEXT_PUBLIC_VERSION || 'development',
      environment: process.env.NODE_ENV
    },
    { status: 200 }
  );
}
