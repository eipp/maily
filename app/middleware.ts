import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const url = request.nextUrl.clone();

  // Handle development environment
  if (process.env.NODE_ENV === 'development') {
    if (url.pathname.startsWith('/marketing')) {
      return NextResponse.next();
    }
    if (hostname.startsWith('app.')) {
      return NextResponse.next();
    }
    return NextResponse.rewrite(new URL('/marketing' + url.pathname, url));
  }

  // Production environment
  if (hostname.includes('justmaily.com')) {
    if (hostname.startsWith('app.')) {
      // Serve app routes directly for app.justmaily.com
      if (url.pathname === '/') {
        return NextResponse.redirect(new URL('/dashboard', url));
      }
      return NextResponse.next();
    } else {
      // Rewrite justmaily.com to marketing routes
      return NextResponse.rewrite(new URL('/marketing' + url.pathname, url));
    }
  }

  // Default behavior
  return NextResponse.next();
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

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)'],
}; 