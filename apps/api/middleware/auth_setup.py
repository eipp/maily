"""Authentication setup for the API."""
import logging
from typing import List
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .standardized_auth import (
    AuthMiddleware,
    AuthProviderBase,
    auth_exception_handler,
)
from .providers import Auth0JWTProvider, DatabaseAPIKeyProvider, VaultServiceTokenProvider
from packages.error_handling.python.error import UnauthorizedError

logger = logging.getLogger(__name__)


def setup_auth_middleware(app: FastAPI) -> None:
    """Set up authentication middleware for the FastAPI app.

    Args:
        app: The FastAPI application.
    """
    # Initialize authentication providers
    providers: List[AuthProviderBase] = []

    # Add providers in order of preference/priority
    try:
        # JWT provider (Auth0)
        providers.append(Auth0JWTProvider())
        logger.info("Auth0 JWT provider initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Auth0 JWT provider: {str(e)}")

    try:
        # API key provider
        providers.append(DatabaseAPIKeyProvider())
        logger.info("API key provider initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize API key provider: {str(e)}")

    try:
        # Service token provider
        providers.append(VaultServiceTokenProvider())
        logger.info("Service token provider initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize service token provider: {str(e)}")

    if not providers:
        logger.error("No authentication providers initialized. Authentication will not work!")

    # Register authentication middleware
    app.add_middleware(AuthMiddleware, providers=providers)

    # Register authentication exception handler
    app.add_exception_handler(UnauthorizedError, auth_exception_handler)

    logger.info(f"Authentication middleware set up with {len(providers)} providers")


async def x_api_key_middleware(request: Request, call_next) -> Response:
    """Middleware to handle X-API-Key header for backward compatibility.

    This middleware converts X-API-Key header to Authorization header for compatibility.

    Args:
        request: The request object.
        call_next: The next middleware handler.

    Returns:
        The response from the next middleware.
    """
    api_key = request.headers.get("X-API-Key")

    if api_key and not request.headers.get("Authorization"):
        # Copy headers to a mutable version
        request.scope["headers"] = [
            (key, value) if key != b"authorization" else (b"authorization", f"Bearer {api_key}".encode())
            for key, value in request.scope["headers"]
        ]

    return await call_next(request)
