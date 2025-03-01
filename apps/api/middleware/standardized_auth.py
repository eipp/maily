"""Standardized Authentication Middleware for the API."""
import logging
from typing import Dict, Any, Optional, List

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from errors.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class JWTVerificationError(Exception):
    """Exception raised when JWT verification fails."""
    pass


class APIKeyVerificationError(Exception):
    """Exception raised when API key verification fails."""
    pass


class AuthProviderBase:
    """Base authentication provider interface."""

    async def verify(self, request: Request) -> Optional[Dict[str, Any]]:
        """Verify authentication and return user information if successful.

        Args:
            request: The request to authenticate.

        Returns:
            User information if authentication is successful, None otherwise.
        """
        raise NotImplementedError("Authentication providers must implement verify")


class JWTProvider(AuthProviderBase):
    """JWT authentication provider."""

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token and return user information.

        Args:
            token: The JWT token to verify.

        Returns:
            User information if the token is valid.

        Raises:
            JWTVerificationError: If token verification fails.
        """
        raise NotImplementedError("JWT provider must implement verify_token")

    async def verify(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract and verify JWT from request.

        Args:
            request: The request to authenticate.

        Returns:
            User information if authentication is successful, None otherwise.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        try:
            return await self.verify_token(token)
        except JWTVerificationError as e:
            logger.debug(f"JWT verification failed: {str(e)}")
            return None


class APIKeyProvider(AuthProviderBase):
    """API key authentication provider."""

    async def verify_key(self, api_key: str) -> Dict[str, Any]:
        """Verify an API key and return user information.

        Args:
            api_key: The API key to verify.

        Returns:
            User information if the key is valid.

        Raises:
            APIKeyVerificationError: If key verification fails.
        """
        raise NotImplementedError("API key provider must implement verify_key")

    async def verify(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract and verify API key from request.

        Args:
            request: The request to authenticate.

        Returns:
            User information if authentication is successful, None otherwise.
        """
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return None

        try:
            return await self.verify_key(api_key)
        except APIKeyVerificationError as e:
            logger.debug(f"API key verification failed: {str(e)}")
            return None


class ServiceTokenProvider(AuthProviderBase):
    """Service-to-service authentication provider."""

    async def verify_service_token(self, token: str) -> Dict[str, Any]:
        """Verify a service token and return service information.

        Args:
            token: The service token to verify.

        Returns:
            Service information if the token is valid.

        Raises:
            JWTVerificationError: If token verification fails.
        """
        raise NotImplementedError("Service provider must implement verify_service_token")

    async def verify(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract and verify service token from request.

        Args:
            request: The request to authenticate.

        Returns:
            Service information if authentication is successful, None otherwise.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        try:
            return await self.verify_service_token(token)
        except JWTVerificationError as e:
            logger.debug(f"Service token verification failed: {str(e)}")
            return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authenticating requests."""

    def __init__(self, app, providers: List[AuthProviderBase]):
        """Initialize the authentication middleware.

        Args:
            app: The FastAPI application.
            providers: A list of authentication providers to use.
        """
        super().__init__(app)
        self.providers = providers

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request through authentication providers.

        Args:
            request: The request to process.
            call_next: The next middleware to call.

        Returns:
            The response from the next middleware.
        """
        # Try each authentication provider in order
        for provider in self.providers:
            try:
                user = await provider.verify(request)
                if user:
                    # Authentication successful, attach user to request
                    request.state.user = user
                    break
            except Exception as e:
                logger.error(f"Authentication error with provider {provider.__class__.__name__}: {str(e)}")

        # Continue with the request even if authentication failed
        # Endpoints requiring authentication will check request.state.user
        return await call_next(request)


async def require_auth(request: Request) -> Dict[str, Any]:
    """Dependency for requiring authentication.

    Args:
        request: The request object.

    Returns:
        The authenticated user.

    Raises:
        AuthenticationError: If no authenticated user is found.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise AuthenticationError("Not authenticated")
    return user


async def require_admin(request: Request) -> Dict[str, Any]:
    """Dependency for requiring admin privileges.

    Args:
        request: The request object.

    Returns:
        The authenticated admin user.

    Raises:
        AuthenticationError: If no authenticated user is found or user is not admin.
    """
    user = await require_auth(request)
    if not user.get("is_admin"):
        raise AuthenticationError("Admin privileges required")
    return user


async def optional_auth(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency for optional authentication.

    Args:
        request: The request object.

    Returns:
        The authenticated user if available, None otherwise.
    """
    return getattr(request.state, "user", None)


# Helper function to convert exceptions to responses
async def auth_exception_handler(request: Request, exc: AuthenticationError) -> Response:
    """Handle authentication errors.

    Args:
        request: The request that caused the exception.
        exc: The authentication exception.

    Returns:
        A JSON response with the error details.
    """
    status_code = 401
    if "Admin privileges required" in str(exc):
        status_code = 403

    return JSONResponse(
        status_code=status_code,
        content={"error": str(exc), "code": "unauthorized"}
    )
