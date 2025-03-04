import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/trust-verification/data/[canvasId]
 * 
 * Fetches complete verification data for a canvas
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
    
    // Call the backend API to get the verification data
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/canvas/${canvasId}/verification/data`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Content-Type': 'application/json',
        // Forward authentication if needed
        ...(request.headers.get('Authorization') 
          ? { 'Authorization': request.headers.get('Authorization')! } 
          : {}),
      },
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `Failed to fetch verification data: ${response.status} ${response.statusText}` 
      }));
      
      return NextResponse.json(
        { error: errorData.message || 'Failed to fetch verification data' },
        { status: response.status }
      );
    }
    
    const verificationData = await response.json();
    
    return NextResponse.json(verificationData);
  } catch (error) {
    console.error('Error fetching verification data:', error);
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}