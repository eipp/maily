import { Redis } from 'ioredis';
import LRUCache from 'lru-cache';
import { logger } from '../utils/logger';
import { config, CacheStorageType } from '../utils/config';
import { PerformanceMetrics } from '../monitoring/metrics';

/**
 * Cache key type
 */
export type CacheKey = string;

/**
 * Cache value type
 */
export type CacheValue = any;

/**
 * Cache options
 */
export interface CacheOptions {
  /**
   * Time-to-live in seconds
   */
  ttl?: number;

  /**
   * Tags for invalidation
   */
  tags?: string[];
}

/**
 * Cache interface
 */
export interface ICache {
  /**
   * Get a value from the cache
   * @param key Cache key
   * @returns Cached value or undefined
   */
  get<T = CacheValue>(key: CacheKey): Promise<T | undefined>;

  /**
   * Set a value in the cache
   * @param key Cache key
   * @param value Value to cache
   * @param options Cache options
   */
  set(key: CacheKey, value: CacheValue, options?: CacheOptions): Promise<void>;

  /**
   * Check if a key exists in the cache
   * @param key Cache key
   * @returns Whether key exists
   */
  has(key: CacheKey): Promise<boolean>;

  /**
   * Delete a value from the cache
   * @param key Cache key
   */
  delete(key: CacheKey): Promise<void>;

  /**
   * Clear all values from the cache
   */
  clear(): Promise<void>;

  /**
   * Invalidate cache entries by tag
   * @param tag Tag to invalidate
   */
  invalidateByTag(tag: string): Promise<void>;
}

/**
 * Memory cache implementation using LRU
 */
export class MemoryCache implements ICache {
  private cache: LRUCache<CacheKey, CacheValue>;
  private tagMap: Map<string, Set<CacheKey>> = new Map();
  private metrics?: PerformanceMetrics;

  /**
   * Create a new memory cache
   * @param options Cache options
   * @param metrics Performance metrics
   */
  constructor(
    options: { maxSize?: number; ttl?: number } = {},
    metrics?: PerformanceMetrics
  ) {
    const maxSize = options.maxSize || config.cache.maxSize;
    const ttl = options.ttl || config.cache.ttl;

    this.cache = new LRUCache({
      max: maxSize,
      ttl: ttl * 1000, // convert to milliseconds
      updateAgeOnGet: true,
    });

    this.metrics = metrics;

    logger.info('Memory cache initialized', { maxSize, ttl });
  }

  /**
   * Get a value from the cache
   * @param key Cache key
   * @returns Cached value or undefined
   */
  async get<T = CacheValue>(key: CacheKey): Promise<T | undefined> {
    const value = this.cache.get(key) as T | undefined;

    if (this.metrics) {
      if (value !== undefined) {
        this.metrics.recordCacheHit(key);
      } else {
        this.metrics.recordCacheMiss(key);
      }
    }

    return value;
  }

  /**
   * Set a value in the cache
   * @param key Cache key
   * @param value Value to cache
   * @param options Cache options
   */
  async set(key: CacheKey, value: CacheValue, options: CacheOptions = {}): Promise<void> {
    // Calculate TTL
    const ttl = options.ttl ? options.ttl * 1000 : undefined;

    // Set in cache
    this.cache.set(key, value, { ttl });

    // Store tags
    if (options.tags) {
      for (const tag of options.tags) {
        if (!this.tagMap.has(tag)) {
          this.tagMap.set(tag, new Set());
        }

        this.tagMap.get(tag)!.add(key);
      }
    }
  }

  /**
   * Check if a key exists in the cache
   * @param key Cache key
   * @returns Whether key exists
   */
  async has(key: CacheKey): Promise<boolean> {
    return this.cache.has(key);
  }

  /**
   * Delete a value from the cache
   * @param key Cache key
   */
  async delete(key: CacheKey): Promise<void> {
    this.cache.delete(key);

    // Clean up tag maps
    for (const [tag, keys] of this.tagMap.entries()) {
      if (keys.has(key)) {
        keys.delete(key);

        // Remove tag if no keys
        if (keys.size === 0) {
          this.tagMap.delete(tag);
        }
      }
    }
  }

  /**
   * Clear all values from the cache
   */
  async clear(): Promise<void> {
    this.cache.clear();
    this.tagMap.clear();
  }

  /**
   * Invalidate cache entries by tag
   * @param tag Tag to invalidate
   */
  async invalidateByTag(tag: string): Promise<void> {
    const keys = this.tagMap.get(tag);

    if (!keys) {
      return;
    }

    // Delete all keys with this tag
    for (const key of keys) {
      this.cache.delete(key);
    }

    // Clear the tag
    this.tagMap.delete(tag);

    logger.debug(`Invalidated cache by tag: ${tag}`, { keysInvalidated: keys.size });
  }
}

/**
 * Redis cache implementation
 */
export class RedisCache implements ICache {
  private client: Redis;
  private prefix: string = 'cache:';
  private tagPrefix: string = 'tag:';
  private defaultTTL: number;
  private metrics?: PerformanceMetrics;

  /**
   * Create a new Redis cache
   * @param redisUrl Redis URL
   * @param options Cache options
   * @param metrics Performance metrics
   */
  constructor(
    redisUrl: string,
    options: { prefix?: string; ttl?: number } = {},
    metrics?: PerformanceMetrics
  ) {
    this.client = new Redis(redisUrl);
    this.prefix = options.prefix || this.prefix;
    this.defaultTTL = options.ttl || config.cache.ttl;
    this.metrics = metrics;

    logger.info('Redis cache initialized', {
      url: redisUrl.replace(/\/\/(.+?):(.+?)@/, '//***:***@'), // Hide credentials
      prefix: this.prefix,
      ttl: this.defaultTTL,
    });

    // Set up error handling
    this.client.on('error', (err) => {
      logger.error('Redis cache error', { error: err.message });
    });
  }

  /**
   * Get a value from the cache
   * @param key Cache key
   * @returns Cached value or undefined
   */
  async get<T = CacheValue>(key: CacheKey): Promise<T | undefined> {
    const prefixedKey = this.getKeyWithPrefix(key);
    const value = await this.client.get(prefixedKey);

    if (this.metrics) {
      if (value !== null) {
        this.metrics.recordCacheHit(key);
      } else {
        this.metrics.recordCacheMiss(key);
      }
    }

    if (value === null) {
      return undefined;
    }

    try {
      return JSON.parse(value) as T;
    } catch (error) {
      logger.error('Error parsing cached value', { key, error });
      return undefined;
    }
  }

  /**
   * Set a value in the cache
   * @param key Cache key
   * @param value Value to cache
   * @param options Cache options
   */
  async set(key: CacheKey, value: CacheValue, options: CacheOptions = {}): Promise<void> {
    const prefixedKey = this.getKeyWithPrefix(key);
    const serializedValue = JSON.stringify(value);

    // Calculate TTL
    const ttl = options.ttl || this.defaultTTL;

    // Store in Redis
    if (ttl) {
      await this.client.set(prefixedKey, serializedValue, 'EX', ttl);
    } else {
      await this.client.set(prefixedKey, serializedValue);
    }

    // Store tags
    if (options.tags && options.tags.length > 0) {
      // Add key to all tag sets
      for (const tag of options.tags) {
        const tagKey = this.getTagKey(tag);
        await this.client.sadd(tagKey, key);

        // Set a reasonable TTL on tag keys to prevent leaks
        // Use a slightly longer TTL than the actual cached item
        await this.client.expire(tagKey, ttl * 1.5);
      }
    }
  }

  /**
   * Check if a key exists in the cache
   * @param key Cache key
   * @returns Whether key exists
   */
  async has(key: CacheKey): Promise<boolean> {
    const prefixedKey = this.getKeyWithPrefix(key);
    const exists = await this.client.exists(prefixedKey);
    return exists === 1;
  }

  /**
   * Delete a value from the cache
   * @param key Cache key
   */
  async delete(key: CacheKey): Promise<void> {
    const prefixedKey = this.getKeyWithPrefix(key);
    await this.client.del(prefixedKey);

    // Clean up tags is harder with Redis
    // We'd need to maintain a reverse index of keys to tags
    // For simplicity, we'll just let tag expiration handle this
  }

  /**
   * Clear all values from the cache
   */
  async clear(): Promise<void> {
    // Find all keys with our prefix
    const keys = await this.client.keys(`${this.prefix}*`);

    if (keys.length > 0) {
      await this.client.del(...keys);
    }

    // Find all tag keys
    const tagKeys = await this.client.keys(`${this.tagPrefix}*`);

    if (tagKeys.length > 0) {
      await this.client.del(...tagKeys);
    }

    logger.info('Cache cleared', {
      keysCleared: keys.length,
      tagsCleared: tagKeys.length,
    });
  }

  /**
   * Invalidate cache entries by tag
   * @param tag Tag to invalidate
   */
  async invalidateByTag(tag: string): Promise<void> {
    const tagKey = this.getTagKey(tag);

    // Get all keys for this tag
    const keys = await this.client.smembers(tagKey);

    if (keys.length > 0) {
      // Delete all keys
      const prefixedKeys = keys.map(k => this.getKeyWithPrefix(k));
      await this.client.del(...prefixedKeys);

      logger.debug(`Invalidated cache by tag: ${tag}`, { keysInvalidated: keys.length });
    }

    // Delete the tag itself
    await this.client.del(tagKey);
  }

  /**
   * Get key with prefix
   * @param key Cache key
   * @returns Prefixed key
   */
  private getKeyWithPrefix(key: CacheKey): string {
    return `${this.prefix}${key}`;
  }

  /**
   * Get tag key
   * @param tag Tag name
   * @returns Tag key
   */
  private getTagKey(tag: string): string {
    return `${this.tagPrefix}${tag}`;
  }

  /**
   * Close the Redis connection
   */
  async close(): Promise<void> {
    await this.client.quit();
  }
}

/**
 * Cache manager for database result caching
 */
export class CacheManager {
  private cache: ICache;
  private metrics?: PerformanceMetrics;
  private isEnabled: boolean;

  /**
   * Create a new cache manager
   * @param options Cache options
   * @param metrics Performance metrics
   */
  constructor(
    options: {
      type?: CacheStorageType;
      redisUrl?: string;
      prefix?: string;
      ttl?: number;
      maxSize?: number;
      enabled?: boolean;
    } = {},
    metrics?: PerformanceMetrics
  ) {
    this.metrics = metrics;
    this.isEnabled = options.enabled !== undefined ? options.enabled : config.cache.enabled;

    if (!this.isEnabled) {
      logger.info('Cache is disabled');
      // Create a dummy cache that does nothing
      this.cache = this.createNoOpCache();
      return;
    }

    const cacheType = options.type || config.cache.storage;

    if (cacheType === CacheStorageType.REDIS) {
      const redisUrl = options.redisUrl || config.cache.redisUrl;

      if (!redisUrl) {
        logger.warn('Redis URL not provided, falling back to memory cache');
        this.cache = new MemoryCache({
          ttl: options.ttl || config.cache.ttl,
          maxSize: options.maxSize || config.cache.maxSize,
        }, metrics);
      } else {
        this.cache = new RedisCache(redisUrl, {
          prefix: options.prefix,
          ttl: options.ttl || config.cache.ttl,
        }, metrics);
      }
    } else {
      this.cache = new MemoryCache({
        ttl: options.ttl || config.cache.ttl,
        maxSize: options.maxSize || config.cache.maxSize,
      }, metrics);
    }
  }

  /**
   * Get the underlying cache
   */
  getCache(): ICache {
    return this.cache;
  }

  /**
   * Check if caching is enabled
   */
  isActive(): boolean {
    return this.isEnabled;
  }

  /**
   * Wrap a function with caching
   * @param fn Function to cache
   * @param keyFn Function to generate cache key
   * @param options Cache options
   * @returns Cached function
   */
  wrap<T>(
    fn: () => Promise<T>,
    keyFn: () => string,
    options: CacheOptions = {}
  ): Promise<T> {
    if (!this.isEnabled) {
      return fn();
    }

    const key = keyFn();

    return this.getOrSet(key, fn, options);
  }

  /**
   * Get a value from cache or compute it
   * @param key Cache key
   * @param fn Function to compute value if not in cache
   * @param options Cache options
   * @returns Cached or computed value
   */
  async getOrSet<T>(
    key: string,
    fn: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    if (!this.isEnabled) {
      return fn();
    }

    // Try to get from cache
    const cachedValue = await this.cache.get<T>(key);

    if (cachedValue !== undefined) {
      return cachedValue;
    }

    // Not in cache, compute value
    const value = await fn();

    // Store in cache
    await this.cache.set(key, value, options);

    return value;
  }

  /**
   * Create a no-op cache (used when caching is disabled)
   */
  private createNoOpCache(): ICache {
    return {
      get: async () => undefined,
      set: async () => {},
      has: async () => false,
      delete: async () => {},
      clear: async () => {},
      invalidateByTag: async () => {},
    };
  }
}

/**
 * Create a singleton cache manager instance
 */
export const cacheManager = new CacheManager({
  type: config.cache.storage,
  redisUrl: config.cache.redisUrl,
  ttl: config.cache.ttl,
  maxSize: config.cache.maxSize,
  enabled: config.cache.enabled,
});

export default cacheManager;
