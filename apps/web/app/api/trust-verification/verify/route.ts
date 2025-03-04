import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/trust-verification/verify
 * 
 * Verifies content on the blockchain
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { canvasId, emailId } = body;
    
    if (!canvasId) {
      return NextResponse.json(
        { error: 'Canvas ID is required' },
        { status: 400 }
      );
    }
    
    // Call the backend API to verify the content
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/canvas/${canvasId}/verification/verify`;
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward authentication if needed
        ...(request.headers.get('Authorization') 
          ? { 'Authorization': request.headers.get('Authorization')! } 
          : {}),
      },
      body: JSON.stringify({ emailId }),
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `Failed to verify content: ${response.status} ${response.statusText}` 
      }));
      
      return NextResponse.json(
        { error: errorData.message || 'Failed to verify content' },
        { status: response.status }
      );
    }
    
    const verificationData = await response.json();
    
    return NextResponse.json(verificationData);
  } catch (error) {
    console.error('Error verifying content:', error);
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}