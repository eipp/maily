/**
 * Rate Limiter Middleware
 * 
 * This middleware implements a token bucket algorithm for rate limiting API requests.
 * It supports configurable rate limits by user tier and distributed rate limiting with Redis.
 */

import { NextFunction, Request, Response } from 'express';
import { RateLimiterRedis, RateLimiterMemory, RateLimiterRes } from 'rate-limiter-flexible';
import Redis from 'ioredis';
import { logger } from '../utils/logger';
import { getUserTier } from '../services/user-service';
import { ApiError } from '../utils/api-error';

// Environment variables
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const RATE_LIMIT_ENABLED = process.env.RATE_LIMIT_ENABLED !== 'false';
const USE_REDIS_RATE_LIMITER = process.env.USE_REDIS_RATE_LIMITER !== 'false';

// Rate limit configurations by user tier
const rateLimitConfigs = {
  free: {
    points: 100, // Number of requests
    duration: 60, // Per minute
  },
  basic: {
    points: 500,
    duration: 60,
  },
  premium: {
    points: 1000,
    duration: 60,
  },
  enterprise: {
    points: 5000,
    duration: 60,
  },
};

// Default rate limit configuration
const defaultRateLimitConfig = {
  points: 60,
  duration: 60,
};

// Redis client for distributed rate limiting
let redisClient: Redis | null = null;

// Rate limiters by user tier
const rateLimiters: Record<string, RateLimiterRedis | RateLimiterMemory> = {};

/**
 * Initialize rate limiters
 */
const initializeRateLimiters = () => {
  if (!RATE_LIMIT_ENABLED) {
    logger.info('Rate limiting is disabled');
    return;
  }
  
  // Initialize Redis client for distributed rate limiting
  if (USE_REDIS_RATE_LIMITER) {
    try {
      redisClient = new Redis(REDIS_URL, {
        enableOfflineQueue: false,
        maxRetriesPerRequest: 3,
      });
      
      redisClient.on('error', (err) => {
        logger.error('Redis error:', err);
      });
      
      logger.info('Redis client initialized for rate limiting');
    } catch (err) {
      logger.error('Failed to initialize Redis client:', err);
      logger.warn('Falling back to in-memory rate limiting');
    }
  } else {
    logger.info('Using in-memory rate limiting');
  }
  
  // Initialize rate limiters for each user tier
  for (const [tier, config] of Object.entries(rateLimitConfigs)) {
    if (USE_REDIS_RATE_LIMITER && redisClient) {
      rateLimiters[tier] = new RateLimiterRedis({
        storeClient: redisClient,
        keyPrefix: `ratelimit:${tier}:`,
        points: config.points,
        duration: config.duration,
      });
    } else {
      rateLimiters[tier] = new RateLimiterMemory({
        keyPrefix: `ratelimit:${tier}:`,
        points: config.points,
        duration: config.duration,
      });
    }
  }
  
  // Initialize default rate limiter
  if (USE_REDIS_RATE_LIMITER && redisClient) {
    rateLimiters.default = new RateLimiterRedis({
      storeClient: redisClient,
      keyPrefix: 'ratelimit:default:',
      points: defaultRateLimitConfig.points,
      duration: defaultRateLimitConfig.duration,
    });
  } else {
    rateLimiters.default = new RateLimiterMemory({
      keyPrefix: 'ratelimit:default:',
      points: defaultRateLimitConfig.points,
      duration: defaultRateLimitConfig.duration,
    });
  }
  
  logger.info('Rate limiters initialized');
};

// Initialize rate limiters on module load
initializeRateLimiters();

/**
 * Get client IP address
 * 
 * @param req Express request
 * @returns Client IP address
 */
const getClientIp = (req: Request): string => {
  // Get IP from X-Forwarded-For header if behind a proxy
  const forwardedFor = req.headers['x-forwarded-for'];
  
  if (forwardedFor) {
    const ips = Array.isArray(forwardedFor)
      ? forwardedFor[0]
      : forwardedFor.split(',')[0];
    
    return ips.trim();
  }
  
  // Fallback to connection remote address
  return req.socket.remoteAddress || '127.0.0.1';
};

/**
 * Get rate limit key
 * 
 * @param req Express request
 * @returns Rate limit key
 */
const getRateLimitKey = (req: Request): string => {
  // Use user ID if authenticated
  if (req.user && req.user.id) {
    return `user:${req.user.id}`;
  }
  
  // Use API key if provided
  if (req.apiKey) {
    return `apikey:${req.apiKey}`;
  }
  
  // Fallback to IP address
  return `ip:${getClientIp(req)}`;
};

/**
 * Get rate limiter for user tier
 * 
 * @param tier User tier
 * @returns Rate limiter
 */
const getRateLimiter = (tier: string): RateLimiterRedis | RateLimiterMemory => {
  return rateLimiters[tier] || rateLimiters.default;
};

/**
 * Rate limiter middleware
 * 
 * @param req Express request
 * @param res Express response
 * @param next Express next function
 */
export const rateLimiter = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  // Skip rate limiting if disabled
  if (!RATE_LIMIT_ENABLED) {
    return next();
  }
  
  try {
    // Get user tier
    const userTier = req.user ? await getUserTier(req.user.id) : 'default';
    
    // Get rate limiter for user tier
    const limiter = getRateLimiter(userTier);
    
    // Get rate limit key
    const key = getRateLimitKey(req);
    
    // Consume a token
    const rateLimiterRes = await limiter.consume(key);
    
    // Set rate limit headers
    setRateLimitHeaders(res, rateLimiterRes, userTier);
    
    next();
  } catch (err) {
    if (err instanceof Error) {
      // Rate limit exceeded
      if (err instanceof RateLimiterRes) {
        setRateLimitHeaders(res, err, req.user ? await getUserTier(req.user.id) : 'default');
        
        return next(new ApiError(429, 'Too Many Requests', 'Rate limit exceeded'));
      }
      
      // Other errors
      logger.error('Rate limiter error:', err);
    }
    
    next();
  }
};

/**
 * Set rate limit headers
 * 
 * @param res Express response
 * @param rateLimiterRes Rate limiter result
 * @param tier User tier
 */
const setRateLimitHeaders = (
  res: Response,
  rateLimiterRes: RateLimiterRes,
  tier: string
) => {
  const config = rateLimitConfigs[tier] || defaultRateLimitConfig;
  
  // Set rate limit headers
  res.setHeader('X-RateLimit-Limit', config.points);
  res.setHeader('X-RateLimit-Remaining', rateLimiterRes.remainingPoints);
  res.setHeader('X-RateLimit-Reset', new Date(Date.now() + rateLimiterRes.msBeforeNext).toISOString());
  
  // Set retry-after header if rate limit exceeded
  if (rateLimiterRes.remainingPoints <= 0) {
    res.setHeader('Retry-After', Math.ceil(rateLimiterRes.msBeforeNext / 1000));
  }
};

/**
 * Cleanup rate limiter resources
 */
export const cleanupRateLimiter = async () => {
  if (redisClient) {
    await redisClient.quit();
    redisClient = null;
  }
};

export default rateLimiter;
