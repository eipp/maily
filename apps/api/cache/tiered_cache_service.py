"""
Tiered Redis caching service with TTL policies.
Provides sophisticated caching with different tiers and expiration strategies.
"""
from typing import Any, Dict, Optional, Union, List, Tuple
from enum import Enum
import json
import time
import hashlib
import structlog
from redis import Redis

logger = structlog.get_logger(__name__)

class CacheTier(str, Enum):
    """Cache tiers with different TTL and eviction policies."""
    FREQUENT = "frequent"     # Frequently accessed data
    STANDARD = "standard"     # Default tier
    EXTENDED = "extended"     # Longer-lived data
    PERMANENT = "permanent"   # Very long-lived data (careful usage)

class CacheService:
    """Service for managing Redis caching with TTL policies.

    Attributes:
        redis: Redis client
        ttl_config: TTL policies by data type
        tier_config: TTL multipliers by tier
    """

    def __init__(self, redis_client: Redis):
        """Initialize cache service.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

        # Define TTL policies by data type (in seconds)
        self.ttl_config = {
            "campaign_content": 3600,     # 1 hour
            "analytics": 300,             # 5 minutes
            "user_preferences": 86400,    # 1 day
            "ai_responses": 43200,        # 12 hours
            "generated_content": 7200,    # 2 hours
            "token_verification": 120,    # 2 minutes
            "session": 1800,              # 30 minutes
            "metadata": 3600,             # 1 hour
            "email_template": 86400,      # 1 day
            "platform_data": 1800,        # 30 minutes
            "api_response": 60,           # 1 minute
            "search_results": 300,        # 5 minutes
            "settings": 86400,            # 1 day
            "user_profile": 1800,         # 30 minutes
            "audit_log": 86400 * 7,       # 7 days
            "system_status": 60,          # 1 minute
        }

        # Define TTL multipliers by tier
        self.tier_config = {
            CacheTier.FREQUENT: 0.5,      # Half the standard TTL
            CacheTier.STANDARD: 1.0,      # Standard TTL
            CacheTier.EXTENDED: 5.0,      # 5x standard TTL
            CacheTier.PERMANENT: 30.0,    # 30x standard TTL (use carefully)
        }

    def get(self, key: str) -> Optional[Any]:
        """Get cached item with deserialization.

        Args:
            key: Cache key

        Returns:
            Deserialized cached data or None if not found
        """
        try:
            # Add monitoring and metrics
            start_time = time.time()

            data = self.redis.get(key)
            if not data:
                logger.debug("Cache miss", key=key)
                return None

            # Try to deserialize JSON
            try:
                result = json.loads(data)
                logger.debug("Cache hit (JSON)", key=key)
            except json.JSONDecodeError:
                # Return as string if not JSON
                result = data.decode("utf-8")
                logger.debug("Cache hit (string)", key=key)

            # Log cache hit with timing
            duration_ms = (time.time() - start_time) * 1000
            logger.debug("Cache operation completed",
                         key=key,
                         operation="get",
                         duration_ms=duration_ms)

            return result

        except Exception as e:
            logger.warning("Cache get error",
                         key=key,
                         error=str(e),
                         error_type=e.__class__.__name__)
            return None

    def set(
        self,
        key: str,
        value: Any,
        data_type: str,
        tier: CacheTier = CacheTier.STANDARD,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set cached item with appropriate TTL.

        Args:
            key: Cache key
            value: Value to cache
            data_type: Type of data (for TTL policy)
            tier: Cache tier (affects TTL)
            nx: Only set if key doesn't exist
            xx: Only set if key already exists

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add monitoring and metrics
            start_time = time.time()

            # Calculate TTL
            base_ttl = self.ttl_config.get(data_type, 3600)  # Default 1 hour
            tier_multiplier = self.tier_config.get(tier, 1.0)
            ttl = int(base_ttl * tier_multiplier)

            # Serialize based on type
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            elif isinstance(value, (int, float, bool)):
                serialized = str(value)
            else:
                serialized = value

            # Set with appropriate parameters
            if nx and xx:
                # Cannot use both options
                logger.warning("Cannot use both nx and xx options", key=key)
                return False
            elif nx:
                result = self.redis.set(key, serialized, ex=ttl, nx=True)
            elif xx:
                result = self.redis.set(key, serialized, ex=ttl, xx=True)
            else:
                result = self.redis.set(key, serialized, ex=ttl)

            # Log operation with timing
            duration_ms = (time.time() - start_time) * 1000
            logger.debug("Cache operation completed",
                        key=key,
                        operation="set",
                        data_type=data_type,
                        tier=tier,
                        ttl=ttl,
                        success=bool(result),
                        duration_ms=duration_ms)

            return bool(result)

        except Exception as e:
            logger.warning("Cache set error",
                         key=key,
                         error=str(e),
                         error_type=e.__class__.__name__)
            return False

    def invalidate(self, pattern: str) -> int:
        """Invalidate all keys matching pattern.

        Args:
            pattern: Redis key pattern to match

        Returns:
            Number of keys removed
        """
        try:
            # Add monitoring and metrics
            start_time = time.time()

            # Get keys matching pattern
            keys = self.redis.keys(pattern)
            if not keys:
                logger.debug("No keys found to invalidate", pattern=pattern)
                return 0

            # Delete keys
            result = self.redis.delete(*keys)

            # Log operation with timing
            duration_ms = (time.time() - start_time) * 1000
            logger.info("Cache invalidation completed",
                       pattern=pattern,
                       keys_count=len(keys),
                       deleted_count=result,
                       duration_ms=duration_ms)

            return result

        except Exception as e:
            logger.warning("Cache invalidation error",
                         pattern=pattern,
                         error=str(e),
                         error_type=e.__class__.__name__)
            return 0

    def get_or_set(
        self,
        key: str,
        data_getter: callable,
        data_type: str,
        tier: CacheTier = CacheTier.STANDARD
    ) -> Any:
        """Get value from cache or generate and store it.

        Args:
            key: Cache key
            data_getter: Function to call if cache miss
            data_type: Type of data (for TTL policy)
            tier: Cache tier (affects TTL)

        Returns:
            Cached or newly generated data
        """
        # Try to get from cache first
        cached = self.get(key)
        if cached is not None:
            return cached

        # Cache miss, generate data
        try:
            generated_data = data_getter()

            # Store in cache
            self.set(key, generated_data, data_type, tier)

            return generated_data

        except Exception as e:
            logger.warning("Cache get_or_set error",
                         key=key,
                         error=str(e),
                         error_type=e.__class__.__name__)
            raise  # Re-raise the exception

    def hash_key(self, base_key: str, params: Dict[str, Any]) -> str:
        """Generate a deterministic hash for parameters to use in cache key.

        Args:
            base_key: Base cache key
            params: Parameters to include in the cache key

        Returns:
            Composite cache key with hashed parameters
        """
        # Serialize parameters in a deterministic way
        param_str = json.dumps(params, sort_keys=True)

        # Generate hash
        param_hash = hashlib.md5(param_str.encode()).hexdigest()

        # Combine base key and hash
        return f"{base_key}:{param_hash}"

    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple cached items.

        Args:
            keys: List of cache keys

        Returns:
            List of deserialized cached data (None for misses)
        """
        try:
            # Add monitoring and metrics
            start_time = time.time()

            # Multi-get from Redis
            results = self.redis.mget(keys)

            # Deserialize results
            deserialized_results = []
            for i, data in enumerate(results):
                if data is None:
                    deserialized_results.append(None)
                    continue

                # Try to deserialize JSON
                try:
                    result = json.loads(data)
                except json.JSONDecodeError:
                    # Return as string if not JSON
                    result = data.decode("utf-8")

                deserialized_results.append(result)

            # Log operation with timing
            duration_ms = (time.time() - start_time) * 1000
            hit_count = sum(1 for r in results if r is not None)
            miss_count = sum(1 for r in results if r is None)

            logger.debug("Cache multi-get completed",
                        keys_count=len(keys),
                        hit_count=hit_count,
                        miss_count=miss_count,
                        hit_ratio=hit_count/len(keys) if keys else 0,
                        duration_ms=duration_ms)

            return deserialized_results

        except Exception as e:
            logger.warning("Cache mget error",
                         keys_count=len(keys),
                         error=str(e),
                         error_type=e.__class__.__name__)
            return [None] * len(keys)

    def pipeline(self) -> "CachePipeline":
        """Create a pipeline for batch operations.

        Returns:
            Cache pipeline
        """
        return CachePipeline(self)

    def health_check(self) -> Dict[str, Any]:
        """Check Redis health and get statistics.

        Returns:
            Health and stats information
        """
        try:
            start_time = time.time()

            # Ping Redis
            ping_result = self.redis.ping()

            # Get info if ping succeeds
            if ping_result:
                info = self.redis.info()
                memory_used = info.get("used_memory_human", "unknown")
                clients_connected = info.get("connected_clients", "unknown")
                uptime_days = info.get("uptime_in_days", "unknown")

                stats = {
                    "status": "healthy" if ping_result else "unhealthy",
                    "memory_used": memory_used,
                    "clients_connected": clients_connected,
                    "uptime_days": uptime_days,
                    "latency_ms": (time.time() - start_time) * 1000
                }
            else:
                stats = {
                    "status": "unhealthy",
                    "error": "Redis ping failed",
                    "latency_ms": (time.time() - start_time) * 1000
                }

            return stats

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": e.__class__.__name__
            }

class CachePipeline:
    """Pipeline for batch cache operations.

    Attributes:
        cache_service: Cache service
        pipeline: Redis pipeline
        operations: List of operations to execute
    """

    def __init__(self, cache_service: CacheService):
        """Initialize pipeline.

        Args:
            cache_service: Cache service
        """
        self.cache_service = cache_service
        self.pipeline = cache_service.redis.pipeline()
        self.operations: List[Tuple[str, Any]] = []

    def set(
        self,
        key: str,
        value: Any,
        data_type: str,
        tier: CacheTier = CacheTier.STANDARD
    ) -> "CachePipeline":
        """Add set operation to pipeline.

        Args:
            key: Cache key
            value: Value to cache
            data_type: Type of data (for TTL policy)
            tier: Cache tier (affects TTL)

        Returns:
            Pipeline for chaining
        """
        # Calculate TTL
        base_ttl = self.cache_service.ttl_config.get(data_type, 3600)
        tier_multiplier = self.cache_service.tier_config.get(tier, 1.0)
        ttl = int(base_ttl * tier_multiplier)

        # Serialize based on type
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value)
        elif isinstance(value, (int, float, bool)):
            serialized = str(value)
        else:
            serialized = value

        # Add to pipeline
        self.pipeline.set(key, serialized, ex=ttl)
        self.operations.append(("set", key))

        return self

    def get(self, key: str) -> "CachePipeline":
        """Add get operation to pipeline.

        Args:
            key: Cache key

        Returns:
            Pipeline for chaining
        """
        self.pipeline.get(key)
        self.operations.append(("get", key))

        return self

    def delete(self, key: str) -> "CachePipeline":
        """Add delete operation to pipeline.

        Args:
            key: Cache key

        Returns:
            Pipeline for chaining
        """
        self.pipeline.delete(key)
        self.operations.append(("delete", key))

        return self

    def execute(self) -> List[Any]:
        """Execute pipeline.

        Returns:
            List of results in order of operations
        """
        try:
            # Add monitoring and metrics
            start_time = time.time()

            # Execute pipeline
            results = self.pipeline.execute()

            # Process results (deserialize gets)
            processed_results = []
            for i, (op_type, op_key) in enumerate(self.operations):
                if op_type == "get" and results[i] is not None:
                    # Try to deserialize JSON
                    try:
                        processed_results.append(json.loads(results[i]))
                    except (json.JSONDecodeError, TypeError):
                        # Return as string if not JSON
                        if isinstance(results[i], bytes):
                            processed_results.append(results[i].decode("utf-8"))
                        else:
                            processed_results.append(results[i])
                else:
                    processed_results.append(results[i])

            # Log operation with timing
            duration_ms = (time.time() - start_time) * 1000
            logger.debug("Cache pipeline executed",
                        operations_count=len(self.operations),
                        duration_ms=duration_ms)

            return processed_results

        except Exception as e:
            logger.warning("Cache pipeline error",
                         operations_count=len(self.operations),
                         error=str(e),
                         error_type=e.__class__.__name__)
            return [None] * len(self.operations)
