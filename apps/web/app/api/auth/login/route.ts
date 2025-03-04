import { NextRequest, NextResponse } from 'next/server';
import { signIn } from 'next-auth/react';
import config from '@/lib/config';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();
    
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Validate credentials against backend API
    const response = await fetch(`${config.urls.api}/auth/validate-credentials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.message || 'Invalid credentials' },
        { status: 401 }
      );
    }

    const userData = await response.json();

    // Create a session token
    return NextResponse.json({
      success: true,
      user: {
        id: userData.id,
        email: userData.email,
        name: userData.name,
        roles: userData.roles || ['user'],
        isAdmin: userData.roles?.includes('admin') || false,
      },
    });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}