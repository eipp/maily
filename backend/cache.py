from typing import Any, Optional, Union
import json
import os
from functools import wraps
import redis
from datetime import timedelta

# Initialize Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    password=os.getenv("REDIS_PASSWORD", ""),
    decode_responses=True
)

class Cache:
    @staticmethod
    def key(*args: Any) -> str:
        """Generate a cache key from arguments."""
        return ":".join(str(arg) for arg in args)

    @staticmethod
    def set(key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a value in cache with optional expiration."""
        try:
            return redis_client.set(
                key,
                json.dumps(value),
                ex=expire.total_seconds() if isinstance(expire, timedelta) else expire
            )
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    @staticmethod
    def delete(key: str) -> bool:
        """Delete a value from cache."""
        try:
            return bool(redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

def cached(expire: Optional[Union[int, timedelta]] = None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = Cache.key(
                func.__name__,
                *(str(arg) for arg in args),
                **{k: str(v) for k, v in kwargs.items()}
            )

            # Try to get from cache
            cached_value = Cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # If not in cache, execute function and cache result
            result = await func(*args, **kwargs)
            Cache.set(cache_key, result, expire)
            return result
        return wrapper
    return decorator

# Example usage:
# from cache import cached, Cache
#
# @cached(expire=timedelta(minutes=5))
# async def get_user_data(user_id: int):
#     # Expensive database query or API call
#     return {"id": user_id, "name": "John Doe"}
#
# # Manual cache usage
# Cache.set("key", "value", expire=300)  # 5 minutes
# value = Cache.get("key") 