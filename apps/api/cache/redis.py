import os
import redis
from loguru import logger

# Import get_secret function - try both possible locations
try:
    from ..dependencies import get_secret
except ImportError:
    try:
        from dependencies import get_secret
    except ImportError:
        # Define a fallback get_secret function if not available
        def get_secret(path: str) -> dict:
            """Fallback get_secret when dependencies module not available."""
            if path == 'redis':
                return {
                    'host': os.getenv("REDIS_HOST", "localhost"),
                    'port': int(os.getenv("REDIS_PORT", "6379")),
                    'password': os.getenv("REDIS_PASSWORD")
                }
            return {}

# Initialize Redis client
redis_client = None

try:
    # First try to get Redis credentials from Vault
    try:
        redis_secrets = get_secret('redis')
        REDIS_HOST = redis_secrets.get('host', 'redis')
        REDIS_PORT = int(redis_secrets.get('port', 6379))
        REDIS_PASSWORD = redis_secrets.get('password')
        logger.info(f"Retrieved Redis credentials from Vault: Host={REDIS_HOST}, Port={REDIS_PORT}")
    except Exception as e:
        logger.warning(f"Failed to retrieve Redis credentials from Vault: {e}")
        logger.warning("Falling back to environment variables for Redis connection")

        # Fallback to environment variables
        REDIS_URL = os.getenv("REDIS_URL")
        if REDIS_URL:
            logger.info(f"Using Redis URL from environment: {REDIS_URL.replace('redis://', '')}")
            # URL format: redis://[:password@]host[:port][/db-number]
            redis_client = redis.from_url(REDIS_URL)
        else:
            REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
            REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
            REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
            REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    # Initialize Redis client if not already initialized from URL
    if redis_client is None:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )

    # Test connection
    redis_client.ping()
    logger.info("Successfully connected to Redis")

except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Log the outcome
if redis_client is None:
    logger.error("Redis client initialization failed")
else:
    logger.info("Redis client initialized and ready")
