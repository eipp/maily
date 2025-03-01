/**
 * Maily API Edge Caching Worker
 *
 * This Cloudflare Worker provides edge caching for the Maily API.
 * It implements intelligent caching strategies, request routing,
 * and performance optimizations at the edge.
 */

// Cache configuration
const CACHE_CONFIG = {
  // Cache TTL for different endpoints (in seconds)
  ttl: {
    default: 60,                // Default TTL: 1 minute
    templates: 3600,            // Templates: 1 hour
    campaigns: 300,             // Campaigns: 5 minutes
    analytics: 600,             // Analytics: 10 minutes
    users: 1800,                // Users: 30 minutes
    settings: 3600,             // Settings: 1 hour
    health: 30,                 // Health checks: 30 seconds
  },
  // Endpoints that should never be cached
  neverCache: [
    '/api/auth',                // Authentication endpoints
    '/api/campaigns/create',    // Campaign creation
    '/api/campaigns/update',    // Campaign updates
    '/api/users/create',        // User creation
    '/api/users/update',        // User updates
    '/api/settings/update',     // Settings updates
  ],
  // Cache key namespace
  namespace: 'maily-api-cache',
};

// Region routing configuration
const REGION_ROUTING = {
  // Map regions to API endpoints
  regions: {
    'us-east': 'https://api-us-east.maily.com',
    'us-west': 'https://api-us-west.maily.com',
    'eu-west': 'https://api-eu-west.maily.com',
    'ap-southeast': 'https://api-ap-southeast.maily.com',
  },
  // Default region if no match
  default: 'us-east',
};

// Rate limiting configuration
const RATE_LIMIT = {
  // Requests per minute
  requestsPerMinute: {
    default: 100,               // Default: 100 requests per minute
    '/api/auth': 20,            // Auth endpoints: 20 requests per minute
    '/api/campaigns/create': 10, // Campaign creation: 10 requests per minute
  },
  // Block duration in seconds when rate limit is exceeded
  blockDuration: 60,
};

/**
 * Main request handler
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event));
});

/**
 * Handle the request
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response
 */
async function handleRequest(event) {
  const request = event.request;
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method;

  // Check rate limits
  const rateLimitResult = await checkRateLimit(request, event);
  if (rateLimitResult) {
    return rateLimitResult;
  }

  // Add security headers to all responses
  const securityHeaders = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; object-src 'none';",
  };

  // Handle preflight requests
  if (method === 'OPTIONS') {
    return handleCors(request);
  }

  // Check if the request should be cached
  if (shouldCache(request)) {
    // Try to get from cache first
    const cacheKey = getCacheKey(request);
    const cache = caches.default;
    let response = await cache.match(cacheKey);

    if (response) {
      // Add cache hit header
      response = new Response(response.body, response);
      response.headers.set('X-Cache', 'HIT');
      response.headers.set('X-Cache-Key', cacheKey);

      // Add security headers
      Object.keys(securityHeaders).forEach(key => {
        response.headers.set(key, securityHeaders[key]);
      });

      return response;
    }

    // Cache miss, fetch from origin
    const originResponse = await fetchFromOrigin(request, event);

    // Only cache successful responses
    if (originResponse.status === 200) {
      // Clone the response for caching
      const clonedResponse = new Response(originResponse.body, originResponse);

      // Add cache miss header
      clonedResponse.headers.set('X-Cache', 'MISS');
      clonedResponse.headers.set('X-Cache-Key', cacheKey);

      // Add security headers
      Object.keys(securityHeaders).forEach(key => {
        clonedResponse.headers.set(key, securityHeaders[key]);
      });

      // Determine TTL based on path
      const ttl = getTtl(path);

      // Cache the response
      event.waitUntil(cache.put(cacheKey, clonedResponse.clone()));

      return clonedResponse;
    }

    // Return the original response for non-200 responses
    return originResponse;
  }

  // For non-cacheable requests, just fetch from origin
  const originResponse = await fetchFromOrigin(request, event);

  // Add security headers
  const response = new Response(originResponse.body, originResponse);
  Object.keys(securityHeaders).forEach(key => {
    response.headers.set(key, securityHeaders[key]);
  });

  return response;
}

/**
 * Determine if a request should be cached
 * @param {Request} request - The request
 * @returns {boolean} - Whether the request should be cached
 */
function shouldCache(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method;

  // Only cache GET requests
  if (method !== 'GET') {
    return false;
  }

  // Check if path is in the never cache list
  for (const neverCachePath of CACHE_CONFIG.neverCache) {
    if (path.startsWith(neverCachePath)) {
      return false;
    }
  }

  // Don't cache requests with Authorization header
  if (request.headers.has('Authorization')) {
    return false;
  }

  return true;
}

/**
 * Get the cache key for a request
 * @param {Request} request - The request
 * @returns {string} - The cache key
 */
function getCacheKey(request) {
  const url = new URL(request.url);

  // Include query parameters in the cache key
  const cacheKey = `${CACHE_CONFIG.namespace}:${url.pathname}${url.search}`;

  return cacheKey;
}

/**
 * Get the TTL for a path
 * @param {string} path - The request path
 * @returns {number} - The TTL in seconds
 */
function getTtl(path) {
  // Check for specific path matches
  for (const [key, value] of Object.entries(CACHE_CONFIG.ttl)) {
    if (key !== 'default' && path.includes(`/${key}`)) {
      return value;
    }
  }

  // Return default TTL if no match
  return CACHE_CONFIG.ttl.default;
}

/**
 * Fetch from the origin server
 * @param {Request} request - The request
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response from the origin
 */
async function fetchFromOrigin(request, event) {
  const url = new URL(request.url);

  // Determine the closest region based on the client's location
  const clientRegion = event.request.cf ? event.request.cf.region : REGION_ROUTING.default;
  let targetRegion = REGION_ROUTING.default;

  // Map client region to closest API region
  if (clientRegion.startsWith('EU')) {
    targetRegion = 'eu-west';
  } else if (clientRegion.startsWith('APAC')) {
    targetRegion = 'ap-southeast';
  } else if (clientRegion.startsWith('WNAM')) {
    targetRegion = 'us-west';
  } else if (clientRegion.startsWith('ENAM')) {
    targetRegion = 'us-east';
  }

  // Get the origin URL for the target region
  const originUrl = REGION_ROUTING.regions[targetRegion];

  // Create a new request with the origin URL
  const originRequest = new Request(
    `${originUrl}${url.pathname}${url.search}`,
    request
  );

  // Add headers to track the request
  originRequest.headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP'));
  originRequest.headers.set('X-Original-URL', request.url);
  originRequest.headers.set('X-Forwarded-Host', url.host);
  originRequest.headers.set('X-Served-By', 'cloudflare-worker');
  originRequest.headers.set('X-Served-Region', targetRegion);

  try {
    // Fetch from origin with a timeout
    const fetchPromise = fetch(originRequest);
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Origin request timed out')), 10000);
    });

    return await Promise.race([fetchPromise, timeoutPromise]);
  } catch (error) {
    // Handle errors
    console.error(`Error fetching from origin: ${error.message}`);

    // Return a 503 Service Unavailable response
    return new Response(
      JSON.stringify({
        error: 'Service Unavailable',
        message: 'The origin server is currently unavailable',
      }),
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': '30',
        },
      }
    );
  }
}

/**
 * Check rate limits for a request
 * @param {Request} request - The request
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response|null>} - Rate limit response or null if not rate limited
 */
async function checkRateLimit(request, event) {
  const url = new URL(request.url);
  const path = url.pathname;
  const clientIp = request.headers.get('CF-Connecting-IP');

  if (!clientIp) {
    return null; // Skip rate limiting if IP is not available
  }

  // Determine rate limit based on path
  let rateLimit = RATE_LIMIT.requestsPerMinute.default;
  for (const [limitPath, limit] of Object.entries(RATE_LIMIT.requestsPerMinute)) {
    if (path.startsWith(limitPath)) {
      rateLimit = limit;
      break;
    }
  }

  // Create a rate limit key that includes the path category
  const pathCategory = path.split('/').slice(0, 3).join('/');
  const rateLimitKey = `ratelimit:${clientIp}:${pathCategory}`;

  // Get current count from KV store
  const kvNamespace = event.env.MAILY_KV;
  let currentCount = 0;

  try {
    const storedValue = await kvNamespace.get(rateLimitKey);
    if (storedValue) {
      currentCount = parseInt(storedValue, 10);
    }
  } catch (error) {
    console.error(`Error reading rate limit from KV: ${error.message}`);
    return null; // Continue if KV read fails
  }

  // Check if rate limit is exceeded
  if (currentCount >= rateLimit) {
    return new Response(
      JSON.stringify({
        error: 'Rate Limit Exceeded',
        message: 'Too many requests, please try again later',
      }),
      {
        status: 429,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': RATE_LIMIT.blockDuration.toString(),
        },
      }
    );
  }

  // Increment the counter
  try {
    await kvNamespace.put(rateLimitKey, (currentCount + 1).toString(), {
      expirationTtl: 60, // Reset after 1 minute
    });
  } catch (error) {
    console.error(`Error writing rate limit to KV: ${error.message}`);
    // Continue even if KV write fails
  }

  return null; // Not rate limited
}

/**
 * Handle CORS preflight requests
 * @param {Request} request - The request
 * @returns {Response} - The CORS response
 */
function handleCors(request) {
  // Get the Origin header
  const origin = request.headers.get('Origin');

  // Check if the origin is allowed
  const allowedOrigins = [
    'https://maily.com',
    'https://app.maily.com',
    'https://admin.maily.com',
    'http://localhost:3000',
  ];

  const corsHeaders = {
    'Access-Control-Allow-Origin': allowedOrigins.includes(origin) ? origin : allowedOrigins[0],
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
    'Access-Control-Max-Age': '86400',
  };

  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
}
