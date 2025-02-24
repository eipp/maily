import os
import redis
from loguru import logger

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

def init_redis():
    """Initialize Redis connection with error handling."""
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        client.ping()  # Test connection
        logger.info("Redis initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        return None

redis_client = init_redis() 