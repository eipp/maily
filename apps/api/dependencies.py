from typing import Generator, Optional, Dict, Any
import os
import json

from fastapi import Depends, HTTPException, status
import hvac
import logging
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

from .cache.redis import redis_client
from .config.settings import settings
from .errors import AuthenticationError, DatabaseError
from .services.database import get_db_connection

logger = logging.getLogger(__name__)

# Configuration - load from env vars
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Here you would typically validate against your user DB
    # For now returning the decoded user_id
    return {"user_id": user_id}

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


async def get_current_user(api_key: str = Depends()):
    """
    Dependency for user authentication using API key.
    
    This implementation performs proper authentication using the api_key_service
    to validate API keys and retrieve the associated user information.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        Dict containing user information including user_id, scopes, and key_id
        
    Raises:
        AuthenticationError: If API key is invalid or expired
    """
    if not api_key:
        raise AuthenticationError("API key is required")
    
    try:
        # Import api_key_service here to avoid circular imports
        from apps.api.services.api_key_service import validate_api_key, get_api_key_scopes
        
        # Validate the API key
        is_valid, key_data = await validate_api_key(api_key)
        
        if not is_valid or not key_data:
            logger.warning("Authentication attempt with invalid API key")
            raise AuthenticationError("Invalid API key")
        
        # Get API key scopes for authorization
        scopes = await get_api_key_scopes(api_key)
        
        # Check if key is expired (should be caught by validate_api_key, but double-check)
        if "expires_at" in key_data and key_data["expires_at"]:
            import dateutil.parser
            expires_at = dateutil.parser.parse(key_data["expires_at"])
            if expires_at < datetime.utcnow():
                logger.warning(f"Authentication attempt with expired API key: {key_data['id']}")
                raise AuthenticationError("API key has expired")
        
        # Return user information
        return {
            "user_id": int(key_data["user_id"]),
            "key_id": key_data["id"],
            "scopes": scopes,
            "authenticated_at": datetime.utcnow().isoformat()
        }
    except ImportError:
        # Fallback for development/testing only
        if os.environ.get("ENVIRONMENT", "").lower() == "production":
            logger.error("API key service not available in production")
            raise AuthenticationError("Authentication service unavailable")
        
        logger.warning("Using development API key validation")
        if not api_key or len(api_key) < 8:
            raise AuthenticationError("Invalid API key")
        
        # For development, return mock user information
        return {
            "user_id": 1,  
            "key_id": "dev_key_1",
            "scopes": ["*"],  # All scopes for development
            "authenticated_at": datetime.utcnow().isoformat()
        }
