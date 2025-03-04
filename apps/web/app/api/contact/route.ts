import { NextRequest, NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request: NextRequest) {
  try {
    const { name, email, company, subject, message } = await request.json();
    
    // Validate required fields
    if (!name || !email || !subject || !message) {
      return NextResponse.json(
        { error: 'Name, email, subject and message are required' },
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

    // Send contact form data to backend API
    const response = await fetch(`${config.urls.api}/contact`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name,
        email,
        company: company || null,
        subject,
        message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.message || 'Failed to submit contact form' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Contact form submitted successfully',
    });
  } catch (error) {
    console.error('Contact form submission error:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}