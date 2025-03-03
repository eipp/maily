"""
API Key management service for secure authentication and authorization.

This module provides functions for creating, validating, and managing API keys
with proper scopes and permissions.
"""

from typing import Dict, Optional, List, Any, Tuple, Union
import logging
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import time
import base64

# Redis for caching
try:
    from apps.api.cache.redis_client import get_redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from models.api_key import ApiKey
from models.user import User
from database.session import get_db
from errors.exceptions import NotFoundError, DatabaseError, AuthenticationError

logger = logging.getLogger(__name__)


async def validate_api_key(api_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate an API key and return its associated data.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Tuple of (is_valid, key_data or None)
    """
    # Try to get from cache first
    if REDIS_AVAILABLE:
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            redis_client = await get_redis_client()
            cached_data = await redis_client.get(f"api_key:{key_hash}")
            
            if cached_data:
                # Key exists in cache, return success with minimal data
                key_data = base64.b64decode(cached_data).decode('utf-8')
                import json
                return True, json.loads(key_data)
        except Exception as e:
            logger.warning(f"Redis error during API key validation: {str(e)}")

    # Fall back to database
    db_user, db_key = await get_user_by_api_key(api_key, return_api_key=True)
    
    if not db_user or not db_key:
        return False, None
        
    # Cache the result for faster future validation
    if REDIS_AVAILABLE and db_key:
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            redis_client = await get_redis_client()
            key_data = {
                "id": str(db_key.id),
                "user_id": str(db_user.id),
                "scopes": db_key.scopes,
                "is_valid": True
            }
            import json
            await redis_client.setex(
                f"api_key:{key_hash}", 
                300,  # 5 minutes TTL
                base64.b64encode(json.dumps(key_data).encode('utf-8'))
            )
        except Exception as e:
            logger.warning(f"Failed to cache API key: {str(e)}")
    
    # Return the key data
    if db_key:
        return True, {
            "id": str(db_key.id),
            "user_id": str(db_user.id),
            "name": db_key.name,
            "scopes": db_key.scopes,
            "expires_at": db_key.expires_at.isoformat() if db_key.expires_at else None,
            "created_at": db_key.created_at.isoformat() if db_key.created_at else None,
            "is_valid": True,
        }
    
    return False, None


async def get_api_key_scopes(api_key: str) -> List[str]:
    """
    Get the scopes associated with an API key.
    
    Args:
        api_key: The API key
        
    Returns:
        List of scope strings
    """
    is_valid, key_data = await validate_api_key(api_key)
    
    if not is_valid or not key_data:
        return []
    
    return key_data.get("scopes", [])


async def get_user_by_api_key(api_key: str, db: Optional[AsyncSession] = None, return_api_key: bool = False) -> Optional[Union[User, Tuple[User, ApiKey]]]:
    """Get a user by API key.

    Args:
        api_key: The API key.
        db: Optional database session.
        return_api_key: Whether to return the API key object along with the user.

    Returns:
        The user if found, None otherwise. If return_api_key is True, returns a tuple of (user, api_key).
    """
    if db is None:
        async with get_db() as session:
            return await _get_user_by_api_key(api_key, session, return_api_key)
    else:
        return await _get_user_by_api_key(api_key, db, return_api_key)


async def _get_user_by_api_key(api_key: str, db: AsyncSession, return_api_key: bool = False) -> Optional[Union[User, Tuple[User, ApiKey]]]:
    """Internal function to get a user by API key.

    Args:
        api_key: The API key.
        db: Database session.
        return_api_key: Whether to return the API key object along with the user.

    Returns:
        The user if found, None otherwise. If return_api_key is True, returns a tuple of (user, api_key).
    """
    try:
        # Check API key format
        if not api_key.startswith("mil_"):
            logger.debug("Invalid API key format (doesn't start with 'mil_')")
            return None

        # Hash the API key for lookup
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

        # Find the API key in the database
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.hashed_key == hashed_key,
                ApiKey.expires_at > datetime.utcnow(),
                ApiKey.is_active == True
            )
        )
        api_key_obj = result.scalars().first()

        if not api_key_obj:
            return None

        # Get the user associated with the API key
        result = await db.execute(
            select(User).where(User.id == api_key_obj.user_id)
        )
        user = result.scalars().first()

        if return_api_key:
            return user, api_key_obj
        else:
            return user
    except Exception as e:
        logger.error(f"Error getting user by API key: {str(e)}")
        return None


async def update_api_key_last_used(api_key_id: str, db: AsyncSession) -> None:
    """Update the last used timestamp of an API key.

    Args:
        api_key_id: The ID of the API key.
        db: Database session.
    """
    try:
        api_key_obj = await db.get(ApiKey, api_key_id)
        if api_key_obj:
            api_key_obj.last_used_at = datetime.utcnow()
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating API key last used: {str(e)}")


async def create_api_key(user_id: str, name: str, db: Optional[AsyncSession] = None, scopes: List[str] = None, expires_in_days: int = 90) -> Dict[str, Any]:
    """Create a new API key for a user.

    Args:
        user_id: The ID of the user.
        name: A name for the API key.
        db: Optional database session.
        scopes: List of scopes to assign to the API key.
        expires_in_days: Number of days until the key expires.

    Returns:
        A dictionary containing the API key and its details.
    """
    if db is None:
        async with get_db() as session:
            return await _create_api_key(user_id, name, session, scopes, expires_in_days)
    else:
        return await _create_api_key(user_id, name, db, scopes, expires_in_days)


async def _create_api_key(user_id: str, name: str, db: AsyncSession, scopes: List[str] = None, expires_in_days: int = 90) -> Dict[str, Any]:
    """Internal function to create a new API key for a user with optional scopes.

    Args:
        user_id: The ID of the user.
        name: A name for the API key.
        db: Database session.
        scopes: Optional list of scopes for the API key.
        expires_in_days: Number of days until the key expires.

    Returns:
        A dictionary containing the API key and its details.
    """
    try:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Generate a new API key
        api_key = f"mil_{secrets.token_urlsafe(32)}"
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

        # Create expiration date
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        api_key_obj = ApiKey(
            user_id=user_id,
            name=name,
            hashed_key=hashed_key,
            scopes=scopes or [],
            expires_at=expires_at,
            is_active=True
        )

        db.add(api_key_obj)
        await db.commit()
        await db.refresh(api_key_obj)

        # Return the API key and its details
        return {
            "id": api_key_obj.id,
            "name": api_key_obj.name,
            "scopes": api_key_obj.scopes,
            "api_key": api_key,  # Only returned once at creation
            "created_at": api_key_obj.created_at,
            "expires_at": api_key_obj.expires_at,
            "is_active": api_key_obj.is_active
        }
    except NotFoundError:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating API key: {str(e)}")
        raise DatabaseError(f"Error creating API key: {str(e)}")


async def revoke_api_key(api_key_id: str, user_id: str, db: Optional[AsyncSession] = None) -> None:
    """Revoke an API key.

    Args:
        api_key_id: The ID of the API key to revoke.
        user_id: The ID of the user who owns the API key.
        db: Optional database session.

    Raises:
        NotFoundError: If the API key is not found.
        AuthenticationError: If the user does not own the API key.
    """
    if db is None:
        async with get_db() as session:
            await _revoke_api_key(api_key_id, user_id, session)
    else:
        await _revoke_api_key(api_key_id, user_id, db)


async def _revoke_api_key(api_key_id: str, user_id: str, db: AsyncSession) -> None:
    """Internal function to revoke an API key.

    Args:
        api_key_id: The ID of the API key to revoke.
        user_id: The ID of the user who owns the API key.
        db: Database session.

    Raises:
        NotFoundError: If the API key is not found.
        AuthenticationError: If the user does not own the API key.
    """
    try:
        # Find the API key
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        api_key = result.scalars().first()

        if not api_key:
            raise NotFoundError(f"API key with ID {api_key_id} not found")

        # Check if the user owns the API key
        if api_key.user_id != user_id:
            raise AuthenticationError("You do not have permission to revoke this API key")

        # Revoke the API key
        api_key.is_active = False

        await db.commit()
        logger.info(f"API key {api_key_id} revoked by user {user_id}")
    except (NotFoundError, AuthenticationError):
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error revoking API key: {str(e)}")
        raise DatabaseError(f"Error revoking API key: {str(e)}")


async def list_api_keys(user_id: str, db: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
    """List all API keys for a user.

    Args:
        user_id: The ID of the user.
        db: Optional database session.

    Returns:
        A list of API key details.
    """
    if db is None:
        async with get_db() as session:
            return await _list_api_keys(user_id, session)
    else:
        return await _list_api_keys(user_id, db)


async def _list_api_keys(user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """Internal function to list all API keys for a user.

    Args:
        user_id: The ID of the user.
        db: Database session.

    Returns:
        A list of API key details.
    """
    try:
        # Find all API keys for the user
        result = await db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id)
        )
        api_keys = result.scalars().all()

        # Format the API keys
        return [
            {
                "id": key.id,
                "name": key.name,
                "scopes": key.scopes,
                "created_at": key.created_at,
                "expires_at": key.expires_at,
                "is_active": key.is_active,
                "last_used_at": key.last_used_at
            }
            for key in api_keys
        ]
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise DatabaseError(f"Error listing API keys: {str(e)}")


def has_scope(api_key_scopes: List[str], required_scope: str) -> bool:
    """Check if an API key has a specific scope.

    Args:
        api_key_scopes: The scopes of the API key.
        required_scope: The scope to check.

    Returns:
        True if the API key has the scope, False otherwise.
    """
    # "*" is a wildcard scope that grants access to everything
    if "*" in api_key_scopes:
        return True
    return required_scope in api_key_scopes
