import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/trust-verification/tokens
 * 
 * Fetches tokens/certificates for the current user or specified user
 */
export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const userId = url.searchParams.get('userId');
    
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID is required' },
        { status: 400 }
      );
    }
    
    // Call the backend API to get the user's tokens
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/trust-verification/tokens`;
    
    const response = await fetch(`${apiUrl}?userId=${userId}`, {
      headers: {
        'Content-Type': 'application/json',
        // Forward authentication
        ...(request.headers.get('Authorization') 
          ? { 'Authorization': request.headers.get('Authorization')! } 
          : {}),
      },
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `Failed to fetch tokens: ${response.status} ${response.statusText}` 
      }));
      
      return NextResponse.json(
        { error: errorData.message || 'Failed to fetch tokens' },
        { status: response.status }
      );
    }
    
    const tokensData = await response.json();
    
    return NextResponse.json(tokensData);
  } catch (error) {
    console.error('Error fetching tokens:', error);
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/trust-verification/tokens
 * 
 * Transfers a token to another user
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tokenId, recipient } = body;
    
    if (!tokenId || !recipient) {
      return NextResponse.json(
        { error: 'Token ID and recipient are required' },
        { status: 400 }
      );
    }
    
    // Call the backend API to transfer the token
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/trust-verification/transfer`;
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward authentication
        ...(request.headers.get('Authorization') 
          ? { 'Authorization': request.headers.get('Authorization')! } 
          : {}),
      },
      body: JSON.stringify({ tokenId, recipient }),
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `Failed to transfer token: ${response.status} ${response.statusText}` 
      }));
      
      return NextResponse.json(
        { error: errorData.message || 'Failed to transfer token' },
        { status: response.status }
      );
    }
    
    const transferData = await response.json();
    
    return NextResponse.json(transferData);
  } catch (error) {
    console.error('Error transferring token:', error);
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}