import Redis from 'ioredis';
import config from '../config';
import logger from './logger';

// Create Redis client
const redisClient = new Redis({
  host: config.redis.host,
  port: config.redis.port,
  password: config.redis.password || undefined,
  retryStrategy: (times: number) => {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  enableReadyCheck: true,
  maxRetriesPerRequest: 3,
});

// Set up event listeners
redisClient.on('connect', () => {
  logger.info('Redis client connected');
});

redisClient.on('ready', () => {
  logger.info('Redis client ready');
});

redisClient.on('error', (err: Error) => {
  logger.error('Redis client error', { error: err.message });
});

redisClient.on('reconnecting', () => {
  logger.warn('Redis client reconnecting');
});

/**
 * Set a value in the cache
 * @param key Cache key
 * @param value Value to store
 * @param ttl Time to live in seconds (optional, uses default from config if not provided)
 */
export const setCache = async <T>(
  key: string,
  value: T,
  ttl: number = config.redis.ttl
): Promise<void> => {
  try {
    const serializedValue = JSON.stringify(value);
    await redisClient.set(key, serializedValue, 'EX', ttl);
  } catch (error: any) {
    logger.error('Error setting cache', { key, error: error.message });
    throw error;
  }
};

/**
 * Get a value from the cache
 * @param key Cache key
 * @returns The value or null if not found
 */
export const getCache = async <T>(key: string): Promise<T | null> => {
  try {
    const value = await redisClient.get(key);

    if (!value) {
      return null;
    }

    return JSON.parse(value) as T;
  } catch (error: any) {
    logger.error('Error getting cache', { key, error: error.message });
    return null;
  }
};

/**
 * Delete a value from the cache
 * @param key Cache key
 */
export const deleteCache = async (key: string): Promise<void> => {
  try {
    await redisClient.del(key);
  } catch (error: any) {
    logger.error('Error deleting cache', { key, error: error.message });
    throw error;
  }
};

/**
 * Clear all cache entries matching a pattern
 * @param pattern Key pattern to match (e.g., 'metrics:*')
 */
export const clearCachePattern = async (pattern: string): Promise<void> => {
  try {
    const keys = await redisClient.keys(pattern);

    if (keys.length > 0) {
      await redisClient.del(...keys);
      logger.info(`Cleared ${keys.length} cache entries matching pattern: ${pattern}`);
    }
  } catch (error: any) {
    logger.error('Error clearing cache pattern', { pattern, error: error.message });
    throw error;
  }
};

/**
 * Check if a key exists in the cache
 * @param key Cache key
 * @returns True if the key exists, false otherwise
 */
export const hasCache = async (key: string): Promise<boolean> => {
  try {
    return (await redisClient.exists(key)) === 1;
  } catch (error: any) {
    logger.error('Error checking cache existence', { key, error: error.message });
    return false;
  }
};

/**
 * Set cache with hash
 * @param key Hash key
 * @param field Hash field
 * @param value Value to store
 * @param ttl Time to live in seconds (optional)
 */
export const setHashCache = async <T>(
  key: string,
  field: string,
  value: T,
  ttl?: number
): Promise<void> => {
  try {
    const serializedValue = JSON.stringify(value);
    await redisClient.hset(key, field, serializedValue);

    if (ttl) {
      await redisClient.expire(key, ttl);
    }
  } catch (error: any) {
    logger.error('Error setting hash cache', { key, field, error: error.message });
    throw error;
  }
};

/**
 * Get cache from hash
 * @param key Hash key
 * @param field Hash field
 * @returns The value or null if not found
 */
export const getHashCache = async <T>(key: string, field: string): Promise<T | null> => {
  try {
    const value = await redisClient.hget(key, field);

    if (!value) {
      return null;
    }

    return JSON.parse(value) as T;
  } catch (error: any) {
    logger.error('Error getting hash cache', { key, field, error: error.message });
    return null;
  }
};

/**
 * Get all fields and values from a hash
 * @param key Hash key
 * @returns Object with all fields and values
 */
export const getAllHashCache = async <T>(key: string): Promise<Record<string, T> | null> => {
  try {
    const values = await redisClient.hgetall(key);

    if (!values || Object.keys(values).length === 0) {
      return null;
    }

    // Parse all values
    const result: Record<string, T> = {};
    for (const [field, value] of Object.entries(values)) {
      result[field] = JSON.parse(value) as T;
    }

    return result;
  } catch (error: any) {
    logger.error('Error getting all hash cache', { key, error: error.message });
    return null;
  }
};

/**
 * Cache decorator for class methods
 * @param ttl Time to live in seconds
 * @param keyPrefix Cache key prefix
 * @returns Decorated method
 */
export function Cacheable(ttl: number = config.redis.ttl, keyPrefix: string = '') {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      // Generate cache key
      const cacheKey = `${keyPrefix}:${propertyKey}:${JSON.stringify(args)}`;

      // Try to get from cache
      const cachedResult = await getCache(cacheKey);

      if (cachedResult !== null) {
        return cachedResult;
      }

      // Execute the original method
      const result = await originalMethod.apply(this, args);

      // Cache the result
      await setCache(cacheKey, result, ttl);

      return result;
    };

    return descriptor;
  };
}

/**
 * Get Redis client health status
 */
export const checkRedisHealth = async (): Promise<{ status: string; details?: Record<string, any> }> => {
  try {
    // Execute a simple PING command
    const pong = await redisClient.ping();

    if (pong !== 'PONG') {
      throw new Error('Redis health check failed: unexpected response');
    }

    // Get server info for details
    const info = await redisClient.info();
    const memory = await redisClient.info('memory');
    const memoryUsed = /used_memory_human:(\S+)/i.exec(memory)?.[1] || 'unknown';

    return {
      status: 'healthy',
      details: {
        memoryUsed,
        uptime: /uptime_in_seconds:(\d+)/i.exec(info)?.[1] || 'unknown',
        connectedClients: /connected_clients:(\d+)/i.exec(info)?.[1] || 'unknown',
        totalKeys: await redisClient.dbsize(),
      },
    };
  } catch (error: any) {
    logger.error('Redis health check failed', { error: error.message });

    return {
      status: 'unhealthy',
      details: {
        error: error.message,
      },
    };
  }
};

// Export the Redis client for direct access if needed
export default redisClient;
