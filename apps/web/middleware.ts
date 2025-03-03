import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  const { pathname, hostname } = url;
  
  // Check if we're on the app subdomain
  const isAppDomain = hostname === 'app.justmaily.com' || 
                      hostname.includes('app.justmaily.') || 
                      (hostname.includes('localhost') && !hostname.includes('landing'));
  
  // Check if we're on the landing page domain
  const isLandingDomain = hostname === 'justmaily.com' || 
                          hostname.includes('justmaily.') && !hostname.includes('app.') || 
                          (hostname.includes('localhost') && hostname.includes('landing'));
  
  // Handle app domain routing
  if (isAppDomain) {
    // If trying to access landing pages on app domain, redirect to main domain
    if (pathname === '/' || 
        pathname === '/pricing' || 
        pathname === '/features' || 
        pathname === '/about' || 
        pathname === '/contact') {
      return NextResponse.redirect(new URL(pathname, 'https://justmaily.com'));
    }
    
    // If on app domain root, redirect to hybrid interface
    if (pathname === '/') {
      return NextResponse.redirect(new URL('/hybrid-interface', request.url));
    }
    
    // Continue with the request for app routes
    return NextResponse.next();
  }
  
  // Handle landing domain routing
  if (isLandingDomain) {
    // If trying to access app pages on landing domain, redirect to app domain
    if (pathname.startsWith('/hybrid-interface') || 
        pathname.startsWith('/dashboard') || 
        pathname.startsWith('/settings')) {
      return NextResponse.redirect(new URL(pathname, 'https://app.justmaily.com'));
    }
    
    // Continue with the request for landing routes
    return NextResponse.next();
  }
  
  // Default behavior for other domains
  return NextResponse.next();
}

// Configure the middleware to run on specific paths
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.jpg$|.*\\.svg$).*)',
  ],
};
