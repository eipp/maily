import { NextRequest, NextResponse } from 'next/server';

// API base URL from environment variable with fallback
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * Proxy handler for AI API requests
 *
 * This route proxies requests from the frontend to the FastAPI backend
 * to avoid CORS issues and to keep API keys secure.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // Construct the backend API URL
    const path = params.path.join('/');
    const searchParams = request.nextUrl.searchParams.toString();
    const url = `${API_BASE_URL}/ai/${path}${searchParams ? `?${searchParams}` : ''}`;

    // Forward the request to the backend
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        // Forward authorization if present
        ...(request.headers.get('Authorization')
          ? { 'Authorization': request.headers.get('Authorization')! }
          : {})
      },
      cache: 'no-store'
    });

    // Get the response data
    const data = await response.json();

    // Return the response
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error proxying AI API request:', error);
    return NextResponse.json(
      { error: 'Failed to fetch data from AI service' },
      { status: 500 }
    );
  }
}

/**
 * POST handler for AI API requests
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // Get the request body
    const body = await request.json();

    // Construct the backend API URL
    const path = params.path.join('/');
    const url = `${API_BASE_URL}/ai/${path}`;

    // Forward the request to the backend
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward authorization if present
        ...(request.headers.get('Authorization')
          ? { 'Authorization': request.headers.get('Authorization')! }
          : {})
      },
      body: JSON.stringify(body),
      cache: 'no-store'
    });

    // Get the response data
    const data = await response.json();

    // Return the response
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error proxying AI API request:', error);
    return NextResponse.json(
      { error: 'Failed to send data to AI service' },
      { status: 500 }
    );
  }
}
