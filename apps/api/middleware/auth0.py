"""Auth0 authentication middleware for FastAPI."""
import json
from typing import Dict, List, Optional, Union

import jwt
import requests
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from config.auth0 import auth0_settings
from config.api_keys import validate_api_key
from models.user import User
from services.user_service import get_user_by_auth0_id


async def get_user_from_api_key(api_key: str) -> Dict:
    """Get user information from API key.

    Args:
        api_key: The API key to validate.

    Returns:
        Dict containing user information associated with the API key.
    """
    # Fetch user info from database based on API key
    from services.api_key_service import get_user_by_api_key

    user = await get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "id": user.id,
        "email": user.email,
        "roles": user.roles,
        "sub": f"api_key|{user.id}"
    }


class Auth0JWTBearer(HTTPBearer):
    """Auth0 JWT Bearer authentication middleware."""

    def __init__(self, auto_error: bool = True):
        """Initialize the Auth0JWTBearer middleware.

        Args:
            auto_error: Whether to raise an exception on authentication failure.
        """
        super().__init__(auto_error=auto_error)
        self.audience = auth0_settings.API_AUDIENCE
        self.jwks_url = f"https://{auth0_settings.DOMAIN}/.well-known/jwks.json"
        self.jwks: Optional[Dict] = None

    async def __call__(self, request: Request):
        # Check API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if validate_api_key(api_key):
                request.state.auth_type = "api_key"
                user_data = await get_user_from_api_key(api_key)
                request.state.user = user_data
                return user_data
            raise HTTPException(status_code=401, detail="Invalid API key")

        credentials = await super().__call__(request)
        try:
            payload = self._verify_jwt(credentials.credentials)

            # Extract user ID from Auth0 subject
            auth0_id = payload.get("sub")
            if not auth0_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject claim",
                )

            # Get user from database using Auth0 ID
            user = await get_user_by_auth0_id(auth0_id)
            if not user:
                # User not found in our database, create a new user record
                # This would typically be handled by a user provisioning service
                from services.user_service import create_user_from_auth0
                user = await create_user_from_auth0(payload)

            # Combine database user data with token claims
            user_data = {
                "id": user.id,
                "email": user.email,
                "roles": user.roles,
                "auth0_id": auth0_id,
                "permissions": payload.get("permissions", []),
                "name": payload.get("name", user.name),
                "picture": payload.get("picture", user.picture)
            }

            request.state.auth_type = "jwt"
            request.state.user = user_data
            return user_data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Could not validate credentials: {str(e)}",
            )

    def _get_jwks(self) -> Dict:
        """Get the JSON Web Key Set from Auth0.

        Returns:
            The JWKS as a dictionary.

        Raises:
            HTTPException: If the JWKS cannot be retrieved.
        """
        try:
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch JWKS: {str(e)}",
            )

    def _verify_jwt(self, token: str) -> Dict:
        """Verify the JWT token and return the decoded payload.

        Args:
            token: The JWT token to verify.

        Returns:
            The decoded JWT payload.

        Raises:
            jwt.PyJWTError: If the token is invalid.
        """
        # Get the kid from the token header
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as e:
            raise jwt.PyJWTError(f"Invalid token header: {str(e)}")

        if not header.get("kid"):
            raise jwt.PyJWTError("Token header missing 'kid'")

        # Find the matching key in the JWKS
        rsa_key = {}
        for key in self.jwks.get("keys", []):
            if key.get("kid") == header.get("kid"):
                rsa_key = {
                    "kty": key.get("kty"),
                    "kid": key.get("kid"),
                    "use": key.get("use"),
                    "n": key.get("n"),
                    "e": key.get("e"),
                }
                break

        if not rsa_key:
            raise jwt.PyJWTError("Unable to find appropriate key in JWKS")

        # Verify the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=auth0_settings.ALGORITHMS,
            audience=self.audience,
            issuer=f"https://{auth0_settings.DOMAIN}/",
        )

        return payload


# Dependency for routes that require authentication
auth0_scheme = Auth0JWTBearer()


async def get_current_user(token: Dict = Depends(auth0_scheme)) -> Dict:
    """Get the current authenticated user from the JWT token.

    Args:
        token: The decoded JWT token with user information.

    Returns:
        The user information from the token.
    """
    return token


async def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    """Check if the current user has admin role.

    Args:
        user: The current user.

    Returns:
        The user if they have admin role.

    Raises:
        HTTPException: If the user doesn't have admin role.
    """
    if "admin" not in user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


async def admin_with_mfa(user: Dict = Depends(require_admin)) -> Dict:
    """Check if the admin user has completed MFA.

    Args:
        user: The current admin user.

    Returns:
        The user if they have completed MFA.

    Raises:
        HTTPException: If the user hasn't completed MFA.
    """
    # Check if user has completed MFA
    # This would typically check a claim in the JWT
    if not user.get("amr", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multi-factor authentication required",
        )
    return user
