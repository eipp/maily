"""Caching system for AI operations."""

import json
import hashlib
from typing import Optional, Any, Dict
from redis import Redis
from loguru import logger

from .errors import CacheError

class AICache:
    """Redis-based cache for AI operations."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        ttl: int = 3600  # 1 hour default TTL
    ):
        """
        Initialize the cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            ttl: Cache TTL in seconds
        """
        try:
            self.redis = Redis(host=host, port=port, db=db)
            self.ttl = ttl
            self.redis.ping()  # Test connection
            logger.info("AI cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI cache: {str(e)}")
            raise CacheError(f"Cache initialization failed: {str(e)}")
            
    def _generate_key(self, prompt: str, params: Dict[str, Any]) -> str:
        """
        Generate a cache key from prompt and parameters.
        
        Args:
            prompt: Input prompt
            params: Generation parameters
            
        Returns:
            Cache key string
        """
        # Create a deterministic string representation of parameters
        param_str = json.dumps(params, sort_keys=True)
        
        # Combine prompt and parameters and hash
        combined = f"{prompt}:{param_str}"
        return f"ai:gen:{hashlib.sha256(combined.encode()).hexdigest()}"
        
    def get(self, prompt: str, params: Dict[str, Any]) -> Optional[str]:
        """
        Get cached generation result.
        
        Args:
            prompt: Input prompt
            params: Generation parameters
            
        Returns:
            Cached result or None if not found
        """
        try:
            key = self._generate_key(prompt, params)
            result = self.redis.get(key)
            if result:
                logger.debug(f"Cache hit for key: {key}")
                return result.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Cache get failed: {str(e)}")
            return None
            
    def set(
        self,
        prompt: str,
        params: Dict[str, Any],
        result: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a generation result.
        
        Args:
            prompt: Input prompt
            params: Generation parameters
            result: Generation result to cache
            ttl: Optional custom TTL in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._generate_key(prompt, params)
            self.redis.set(
                key,
                result.encode('utf-8'),
                ex=ttl or self.ttl
            )
            logger.debug(f"Cached result for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache set failed: {str(e)}")
            return False
            
    def clear(self) -> bool:
        """Clear all cached results."""
        try:
            pattern = "ai:gen:*"
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(cursor, pattern)
                if keys:
                    self.redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
            return False 