import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email } = body;

    // Validate input
    if (!email) {
      return NextResponse.json(
        { detail: 'Email is required' },
        { status: 400 }
      );
    }

    // Call the backend API to send password reset email
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/password-reset`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    // For security reasons, always return success even if the email doesn't exist
    // This prevents email enumeration attacks
    if (response.status === 404) {
      return NextResponse.json({}, { status: 204 });
    }

    // Handle other API responses
    if (!response.ok) {
      const data = await response.json();
      return NextResponse.json(
        { detail: data.detail || 'Failed to send password reset email' },
        { status: response.status }
      );
    }

    return NextResponse.json({}, { status: 204 });
  } catch (error) {
    console.error('Password reset error:', error);
    return NextResponse.json(
      { detail: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
