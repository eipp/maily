import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/trust-verification/badge/[canvasId]
 * 
 * Fetches a verification badge for a specific canvas
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { canvasId: string } }
) {
  try {
    const { canvasId } = params;
    
    if (!canvasId) {
      return NextResponse.json(
        { error: 'Canvas ID is required' },
        { status: 400 }
      );
    }
    
    // Call the backend API to get the verification badge
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/canvas/${canvasId}/verification/badge`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Content-Type': 'application/json',
        // Forward authentication if needed
        ...(request.headers.get('Authorization') 
          ? { 'Authorization': request.headers.get('Authorization')! } 
          : {}),
      },
      // Required for passing cookies in server components
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `Failed to fetch verification badge: ${response.status} ${response.statusText}` 
      }));
      
      return NextResponse.json(
        { error: errorData.message || 'Failed to fetch verification badge' },
        { status: response.status }
      );
    }
    
    const badgeData = await response.json();
    
    return NextResponse.json(badgeData);
  } catch (error) {
    console.error('Error fetching verification badge:', error);
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}