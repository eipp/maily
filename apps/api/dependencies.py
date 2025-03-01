from typing import Generator, Optional, Dict, Any
import os
import json

from fastapi import Depends, HTTPException
import hvac
import logging

from .cache.redis import redis_client
from .config.settings import settings
from .errors import AuthenticationError, DatabaseError
from .services.database import get_db_connection

logger = logging.getLogger(__name__)


def get_secret(path: str) -> dict:
    """Fetch secrets from Vault."""
    try:
        # First check if we're running with Vault Agent and try to read from its template files
        try:
            # For database credentials
            if path == 'database' and os.getenv('VAULT_AGENT_ENABLED', 'false').lower() == 'true':
                agent_db_file = os.getenv('VAULT_AGENT_DB_FILE', '/vault/agent-data/db-creds.json')
                if os.path.exists(agent_db_file):
                    with open(agent_db_file, 'r') as f:
                        db_creds = json.load(f)

                    return {
                        'username': db_creds['db']['username'],
                        'password': db_creds['db']['password'],
                        'host': db_creds['db']['host'],
                        'port': db_creds['db']['port'],
                        'dbname': db_creds['db']['database']
                    }

            # For Redis credentials
            if path == 'redis' and os.getenv('VAULT_AGENT_ENABLED', 'false').lower() == 'true':
                agent_redis_file = os.getenv('VAULT_AGENT_REDIS_FILE', '/vault/agent-data/redis-creds.json')
                if os.path.exists(agent_redis_file):
                    with open(agent_redis_file, 'r') as f:
                        redis_creds = json.load(f)

                    return {
                        'host': redis_creds['redis']['host'],
                        'port': redis_creds['redis']['port'],
                        'password': redis_creds['redis']['password']
                    }
        except Exception as agent_err:
            # Log error but continue with direct Vault API approach
            logger.warning(f"Failed to read from Vault Agent template: {agent_err}")

        # Direct Vault API approach
        client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
        if not client.is_authenticated():
            raise DatabaseError("Failed to authenticate with Vault")

        # For database, try dynamic credentials first if configured
        if path == 'database' and os.getenv('VAULT_USE_DYNAMIC_DB', 'false').lower() == 'true':
            try:
                # Try to get dynamic credentials from database secrets engine
                db_creds = client.secrets.database.generate_credentials(
                    name="api-service",
                    mount_point="database"
                )

                # Get static database connection info
                db_config = client.secrets.kv.v2.read_secret_version(
                    path="api/database",
                    mount_point="secret"
                )['data']['data']

                return {
                    'username': db_creds['data']['username'],
                    'password': db_creds['data']['password'],
                    'host': db_config['host'],
                    'port': db_config['port'],
                    'dbname': db_config['dbname']
                }
            except Exception as db_err:
                logger.warning(f"Failed to get dynamic database credentials: {db_err}, falling back to KV store")

        # Standard KV lookup for all other cases
        return client.secrets.kv.v2.read_secret_version(path=path)['data']['data']
    except Exception as e:
        # For development fallback when Vault is not available
        if path == 'database':
            return {
                'username': 'postgres',
                'password': 'postgres',
                'host': 'db',
                'port': 5432,
                'dbname': 'maily'
            }
        elif path == 'redis':
            return {
                'host': 'redis',
                'port': 6379,
                'password': None
            }
        raise DatabaseError(f"Failed to retrieve secret from Vault: {str(e)}")


async def get_db() -> Generator:
    """Dependency for database connection."""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            conn.close()


def get_model_service(model_name: str = Depends()):
    """
    Dependency for model service.

    Returns the AI service instance.
    """
    from apps.api.ai import AIService

    # Create a singleton instance if it doesn't exist
    if not hasattr(get_model_service, "_instance"):
        get_model_service._instance = AIService()

    return get_model_service._instance


def get_redis():
    """Dependency for Redis client."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    return redis_client


def get_current_user(api_key: str = Depends()):
    """Dependency for user authentication."""
    if not api_key or api_key != settings.API_KEY:
        raise AuthenticationError("Invalid API key")
    return {"user_id": 1}  # TODO: Implement proper user authentication
