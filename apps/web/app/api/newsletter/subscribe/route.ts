import { NextRequest, NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();
    
    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Please provide a valid email address' },
        { status: 400 }
      );
    }

    // Call API to subscribe user to newsletter
    const response = await fetch(`${config.urls.api}/newsletter/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      
      // Handle specific error cases
      if (response.status === 409) {
        return NextResponse.json(
          { error: 'This email is already subscribed to our newsletter' },
          { status: 409 }
        );
      }
      
      return NextResponse.json(
        { error: errorData.message || 'Failed to subscribe to newsletter' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Successfully subscribed to newsletter',
    });
  } catch (error) {
    console.error('Newsletter subscription error:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}