"""Authentication middleware for the API."""
import logging
import os
from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from services.user_service import get_user_by_auth0_id, create_user_from_auth0
from services.api_key_service import get_user_by_api_key

logger = logging.getLogger(__name__)

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_ALGORITHMS = ["RS256"]

# Security scheme for JWT authentication
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get the current user from the request.

    This function handles both JWT and API key authentication.

    Args:
        credentials: The authorization credentials.
        db: The database session.

    Returns:
        The user information.

    Raises:
        HTTPException: If authentication fails.
    """
    # Check if the token is a JWT or an API key
    token = credentials.credentials

    # Try JWT authentication first
    try:
        return await _authenticate_with_jwt(token, db)
    except HTTPException as jwt_error:
        # If JWT authentication fails, try API key authentication
        try:
            return await _authenticate_with_api_key(token, db)
        except HTTPException as api_key_error:
            # If both authentication methods fail, raise the JWT error
            # This provides better security by not revealing if the token was a valid API key format
            raise jwt_error


async def _authenticate_with_jwt(token: str, db: AsyncSession) -> Dict[str, Any]:
    """Authenticate a user with a JWT token.

    Args:
        token: The JWT token.
        db: The database session.

    Returns:
        The user information.

    Raises:
        HTTPException: If authentication fails.
    """
    if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
        logger.error("Auth0 configuration is missing")
        raise HTTPException(
            status_code=500,
            detail="Authentication configuration error"
        )

    try:
        # Verify and decode the JWT
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks_client = jwt.PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )

        # Extract user information from the token
        auth0_id = payload.get("sub")
        if not auth0_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

        # Get the user from the database
        user = await get_user_by_auth0_id(auth0_id, db)

        # If the user doesn't exist, create a new user
        if not user:
            # Extract user information from the token
            email = payload.get("email")
            name = payload.get("name")

            if not email:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials"
                )

            # Create a new user
            user = await create_user_from_auth0(
                auth0_id=auth0_id,
                email=email,
                name=name,
                db=db
            )

        # Return the user information
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "auth0_id": auth0_id
        }
    except JWTError as e:
        logger.error(f"JWT authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Authentication error"
        )


async def _authenticate_with_api_key(api_key: str, db: AsyncSession) -> Dict[str, Any]:
    """Authenticate a user with an API key.

    Args:
        api_key: The API key.
        db: The database session.

    Returns:
        The user information.

    Raises:
        HTTPException: If authentication fails.
    """
    try:
        # Get the user from the database
        user = await get_user_by_api_key(api_key, db)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

        # Return the user information
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "auth_method": "api_key"
        }
    except Exception as e:
        logger.error(f"API key authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require the user to be an admin.

    Args:
        user: The user information.

    Returns:
        The user information if the user is an admin.

    Raises:
        HTTPException: If the user is not an admin.
    """
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return user


async def optional_auth(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """Optional authentication middleware.

    This function attempts to authenticate the user, but does not raise an exception if authentication fails.

    Args:
        request: The request object.
        db: The database session.

    Returns:
        The user information if authentication succeeds, None otherwise.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None

        # Try JWT authentication first
        try:
            return await _authenticate_with_jwt(token, db)
        except HTTPException:
            # If JWT authentication fails, try API key authentication
            try:
                return await _authenticate_with_api_key(token, db)
            except HTTPException:
                return None
    except Exception:
        return None
