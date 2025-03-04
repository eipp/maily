# Standardized Redis Client

This directory contains the standardized Redis client implementation for all Maily services.

## Features

- Connection pooling for efficient resource usage
- Circuit breaker pattern for resilience
- Standardized error handling
- Support for all Redis operations
- Development/testing mode with dummy implementation
- Comprehensive metrics and monitoring

## Usage

```python
from packages.database.src.redis-client import get_redis_client, close_redis

# Get the Redis client
redis_client = await get_redis_client()

# Use the client
await redis_client.set("key", "value")
value = await redis_client.get("key")

# Use the pipeline for batch operations
async with redis_client.pipeline() as pipe:
    pipe.set("key1", "value1")
    pipe.set("key2", "value2")
    await pipe.execute()

# Close the client when done
await close_redis()
```

## Configuration

The client is configured using environment variables:

- `REDIS_URL`: Redis URL in format `redis://host:port/db`
- `REDIS_HOST`: Redis host (default: "localhost")
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)
- `REDIS_PASSWORD`: Redis password (optional)
- `REDIS_POOL_SIZE`: Connection pool size (default: 10)
- `REDIS_CB_FAILURE_THRESHOLD`: Circuit breaker failure threshold (default: 5)
- `REDIS_CB_RESET_TIMEOUT`: Circuit breaker reset timeout in seconds (default: 30.0)
- `REDIS_CB_HALF_OPEN_TIMEOUT`: Circuit breaker half-open timeout in seconds (default: 5.0)
- `REDIS_DEFAULT_TIMEOUT`: Default operation timeout in seconds (default: 1.0)

## Migration

All services should use this standardized client. Legacy Redis clients at `apps/api/cache/redis.py` and `apps/api/cache/redis_service.py` have been replaced with wrappers that use this implementation.

New code should import directly from this module rather than using the legacy wrappers.