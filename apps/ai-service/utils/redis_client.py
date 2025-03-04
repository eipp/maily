"""
Redis client for AI service (using shared implementation).

This module provides a thin wrapper around the shared Redis client
implementation, maintaining API compatibility for existing code.
It also adds rate limiting functionality for the AI Mesh Network.
"""

import logging
import time
import asyncio
from typing import Optional, Union, Dict, Any, Tuple

from packages.database.src.redis import (
    get_redis_client as get_shared_redis_client,
    close_redis,
    RedisClient,
    DummyRedisClient,
)

logger = logging.getLogger("ai_service.utils.redis_client")

# Re-export the get_redis_client function to maintain API compatibility
async def get_redis_client() -> Union[RedisClient, DummyRedisClient]:
    """
    Get a Redis client instance.
    
    Returns:
        A Redis client instance from the shared implementation.
    """
    return await get_shared_redis_client()

# Alias for backward compatibility
init_redis = get_redis_client

class TokenBucketRateLimiter:
    """
    Redis-based token bucket rate limiter.
    
    This implements a distributed rate limiter using Redis to maintain state
    across multiple instances. It follows the token bucket algorithm:
    - A bucket has a maximum capacity of tokens
    - Tokens are added at a constant rate (refill_rate)
    - Each operation consumes one or more tokens
    - If the bucket doesn't have enough tokens, the operation is rate-limited
    """
    
    def __init__(self, redis_client, key_prefix: str = "rate_limit:"):
        """
        Initialize the rate limiter.
        
        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.lua_script_sha = None
    
    async def setup(self):
        """Set up the rate limiter, loading the Lua script into Redis"""
        # Define the Lua script for atomic token bucket operations
        lua_script = """
        local key = KEYS[1]
        local tokens_to_consume = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])
        local refill_interval_seconds = tonumber(ARGV[4])
        local now = tonumber(ARGV[5])
        
        -- If the bucket doesn't exist, create it
        local exists = redis.call('EXISTS', key)
        if exists == 0 then
            -- Initialize a new bucket with max capacity
            redis.call('HMSET', key, 
                'tokens', capacity, 
                'last_refill', now,
                'capacity', capacity,
                'refill_rate', refill_rate,
                'refill_interval', refill_interval_seconds
            )
            -- Set TTL to prevent abandoned keys from accumulating
            redis.call('EXPIRE', key, 86400)
        end
        
        -- Get the current state
        local bucket = redis.call('HGETALL', key)
        local tokens = tonumber(bucket[2])
        local last_refill = tonumber(bucket[4])
        local capacity = tonumber(bucket[6])
        local refill_rate = tonumber(bucket[8])
        local refill_interval = tonumber(bucket[10])
        
        -- Calculate tokens to refill based on time elapsed
        local time_passed = now - last_refill
        local intervals = math.floor(time_passed / refill_interval)
        local tokens_to_add = intervals * refill_rate
        
        -- If time has passed, refill the bucket
        if tokens_to_add > 0 then
            tokens = math.min(capacity, tokens + tokens_to_add)
            redis.call('HSET', key, 'tokens', tokens, 'last_refill', last_refill + (intervals * refill_interval))
        end
        
        -- Check if we have enough tokens
        local allowed = 0
        local wait_time = 0
        local new_tokens = tokens
        
        if tokens >= tokens_to_consume then
            -- Allow the request and consume tokens
            allowed = 1
            new_tokens = tokens - tokens_to_consume
            redis.call('HSET', key, 'tokens', new_tokens)
        else
            -- Calculate wait time until enough tokens would be available
            local tokens_needed = tokens_to_consume - tokens
            local intervals_needed = math.ceil(tokens_needed / refill_rate)
            wait_time = intervals_needed * refill_interval
        end
        
        -- Refresh TTL
        redis.call('EXPIRE', key, 86400)
        
        -- Return result [allowed, remaining tokens, wait time, capacity]
        return {allowed, new_tokens, wait_time, capacity}
        """
        
        # Load script into Redis and store the SHA
        self.lua_script_sha = await self.redis.script_load(lua_script)
        logger.info(f"Rate limiter Lua script loaded with SHA: {self.lua_script_sha}")
    
    async def check_rate_limit(
        self,
        key: str,
        tokens: int = 1,
        capacity: int = 100,
        refill_rate: int = 10,
        refill_interval_seconds: int = 1,
        wait: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if an action is within rate limits.
        
        Args:
            key: Rate limit key (e.g., user_id, api_key, endpoint)
            tokens: Number of tokens to consume
            capacity: Maximum capacity of the bucket
            refill_rate: Number of tokens to add per interval
            refill_interval_seconds: Interval for token refill in seconds
            wait: Whether to wait if rate limited
            
        Returns:
            Tuple (allowed, info)
                - allowed: Whether the action is allowed
                - info: Additional information (remaining, wait_time)
        """
        if self.lua_script_sha is None:
            await self.setup()
        
        # Full Redis key with prefix
        redis_key = f"{self.key_prefix}{key}"
        
        # Current timestamp
        now = int(time.time())
        
        try:
            # Execute the Lua script
            result = await self.redis.evalsha(
                self.lua_script_sha,
                1,  # Number of keys
                redis_key,  # Keys
                tokens, capacity, refill_rate, refill_interval_seconds, now  # Arguments
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            wait_time = int(result[2])
            total = int(result[3])
            
            info = {
                "allowed": allowed,
                "remaining": remaining,
                "wait_time_seconds": wait_time,
                "total": total,
                "key": key
            }
            
            # If rate limited and asked to wait, sleep for wait_time
            if not allowed and wait and wait_time > 0:
                # Cap maximum wait time to avoid excessive delays
                max_wait = 60  # Maximum 60 seconds wait
                actual_wait = min(wait_time, max_wait)
                logger.info(f"Rate limited for {key}, waiting {actual_wait}s")
                await asyncio.sleep(actual_wait)
                # Recursively check again after waiting
                return await self.check_rate_limit(key, tokens, capacity, refill_rate, refill_interval_seconds, False)
            
            return allowed, info
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow the request to proceed
            return True, {"error": str(e), "allowed": True}
    
    async def reset_limit(self, key: str) -> bool:
        """
        Reset rate limit for a key.
        
        Args:
            key: Rate limit key to reset
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis_key = f"{self.key_prefix}{key}"
            result = await self.redis.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

# Singleton instance
_rate_limiter_instance = None

async def get_rate_limiter() -> TokenBucketRateLimiter:
    """Get a singleton instance of TokenBucketRateLimiter"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        redis_client = await get_redis_client()
        _rate_limiter_instance = TokenBucketRateLimiter(redis_client)
        await _rate_limiter_instance.setup()
    return _rate_limiter_instance