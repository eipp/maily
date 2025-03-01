/**
 * Redis-based email rate limiter implementation
 */
import { EmailRateLimiter } from '../../application/usecases/email-service';
import { Redis } from 'ioredis';

/**
 * Redis-based implementation of rate limiting for email sending
 */
export class RedisEmailRateLimiter implements EmailRateLimiter {
  /**
   * Creates a new RedisEmailRateLimiter instance
   * @param redisClient Redis client for storing rate limit data
   * @param limits Rate limits configuration by provider
   * @param durationSeconds Duration in seconds for the rate limit window (default: 86400 - one day)
   */
  constructor(
    private readonly redisClient: Redis,
    private readonly limits: Record<string, number>,
    private readonly durationSeconds: number = 86400
  ) {}

  /**
   * Checks if sending is allowed based on rate limits
   * @param provider Email provider name
   * @param userId User ID or identifier
   * @returns True if sending is allowed, false if rate limited
   */
  async allowSend(provider: string, userId: string): Promise<boolean> {
    const limit = this.limits[provider] || 1000; // Default daily limit
    const key = `rate:email:${provider}:${userId}:${this.getDateKey()}`;

    // Use Redis to increment and check the counter atomically
    const count = await this.redisClient.incr(key);

    if (count === 1) {
      // Set expiry for new keys
      await this.redisClient.expire(key, this.durationSeconds);
    }

    return count <= limit;
  }

  /**
   * Gets the current count for a user/provider
   * @param provider Email provider name
   * @param userId User ID or identifier
   * @returns Current count of emails sent in the current period
   */
  async getCurrentCount(provider: string, userId: string): Promise<number> {
    const key = `rate:email:${provider}:${userId}:${this.getDateKey()}`;
    const count = await this.redisClient.get(key);
    return count ? parseInt(count, 10) : 0;
  }

  /**
   * Gets remaining quota for a user/provider
   * @param provider Email provider name
   * @param userId User ID or identifier
   * @returns Remaining email quota
   */
  async getRemainingQuota(provider: string, userId: string): Promise<number> {
    const limit = this.limits[provider] || 1000;
    const currentCount = await this.getCurrentCount(provider, userId);
    return Math.max(0, limit - currentCount);
  }

  /**
   * Gets the date key for the current period
   * @returns Formatted date string for the current period
   */
  private getDateKey(): string {
    const now = new Date();
    return `${now.getUTCFullYear()}-${now.getUTCMonth() + 1}-${now.getUTCDate()}`;
  }
}
