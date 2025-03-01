import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// A/B testing configuration
const TEST_VARIANTS = {
  'homepage-design': ['control', 'variant-a', 'variant-b'],
  'pricing-layout': ['control', 'variant-a'],
};

// Mock geo-targeted content (would come from a CMS or API in production)
const GEO_CONTENT = {
  'US': { currency: 'USD', greeting: 'Hello' },
  'UK': { currency: 'GBP', greeting: 'Hello' },
  'FR': { currency: 'EUR', greeting: 'Bonjour' },
  'DE': { currency: 'EUR', greeting: 'Hallo' },
  'default': { currency: 'USD', greeting: 'Welcome' },
};

export const config = {
  matcher: [
    // Run on all paths except for API routes, static files, and public assets
    '/((?!api/|_next/|_static/|_vercel|[\\w-]+\\.\\w+).*)',
  ],
};

export default async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // 1. Geolocation-based handling
  const country = request.geo?.country || 'default';
  const geoContent = GEO_CONTENT[country] || GEO_CONTENT.default;

  // Add geo information as headers for client and server components
  response.headers.set('x-maily-country', country);
  response.headers.set('x-maily-currency', geoContent.currency);
  response.headers.set('x-maily-greeting', geoContent.greeting);

  // 2. A/B Testing implementation
  const url = request.nextUrl;

  // Only apply A/B tests to specific pages
  if (url.pathname === '/' || url.pathname === '/pricing') {
    const testName = url.pathname === '/' ? 'homepage-design' : 'pricing-layout';
    const variants = TEST_VARIANTS[testName];

    // Check if user already has a variant assigned in cookie
    const variantCookie = request.cookies.get(`ab-test-${testName}`)?.value;

    let variant: string;

    if (variantCookie && variants.includes(variantCookie)) {
      // Use existing variant
      variant = variantCookie;
    } else {
      // Assign a variant randomly
      variant = variants[Math.floor(Math.random() * variants.length)];

      // Set the variant in a cookie
      response.cookies.set(`ab-test-${testName}`, variant, {
        maxAge: 60 * 60 * 24 * 7, // 1 week
        path: '/',
      });
    }

    // Add variant info as a header
    response.headers.set(`x-maily-ab-${testName}`, variant);
  }

  // 3. Authentication checking
  const authToken = request.cookies.get('auth-token')?.value;

  // Protected routes that require authentication
  const isProtectedRoute = url.pathname.startsWith('/dashboard') ||
                          url.pathname.startsWith('/account') ||
                          url.pathname.startsWith('/settings');

  // API key validation for API routes (simple check, would be more robust in production)
  const isApiRoute = url.pathname.startsWith('/api/');
  const apiKey = request.headers.get('x-api-key');

  if (isApiRoute && !apiKey) {
    return new NextResponse(
      JSON.stringify({ success: false, message: 'API key required' }),
      { status: 401, headers: { 'content-type': 'application/json' } }
    );
  }

  // Redirect to login if accessing protected route without auth
  if (isProtectedRoute && !authToken) {
    const loginUrl = new URL('/auth/login', request.url);
    loginUrl.searchParams.set('from', url.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 4. Basic security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  // 5. Edge caching for static pages
  if (!isProtectedRoute && !isApiRoute && request.method === 'GET') {
    response.headers.set('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
  }

  return response;
}

// In-memory store for rate limiting
// Note: For production, use Redis or similar
const requestCounts = new Map<string, number[]>();

// Clean up old rate limit data periodically
setInterval(() => {
  const now = Date.now();
  const windowMs = parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10);

  for (const [ip, times] of requestCounts.entries()) {
    const validTimes = times.filter(time => now - time < windowMs);
    if (validTimes.length === 0) {
      requestCounts.delete(ip);
    } else {
      requestCounts.set(ip, validTimes);
    }
  }
}, 60000); // Clean up every minute
