"""Error handling middleware for FastAPI."""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ..errors import (
    AIError,
    AuthError,
    DatabaseError,
    MailyError,
    RateLimitError,
    ValidationError,
)

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Middleware to catch and handle all errors in a consistent way."""
    try:
        return await call_next(request)
    except MailyError as e:
        logger.error(f"MailyError: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={"error": str(e), "type": e.__class__.__name__},
        )
    except Exception as e:
        logger.critical(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An unexpected error occurred",
                "type": "InternalServerError",
            },
        )


def register_error_handlers(app):
    """Register error handlers for specific error types."""

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        logger.warning(f"Authentication error: {str(exc)}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc), "type": "AuthError"},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.warning(f"Validation error: {str(exc)}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc), "type": "ValidationError"},
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc), "type": "DatabaseError"},
        )

    @app.exception_handler(AIError)
    async def ai_error_handler(request: Request, exc: AIError):
        logger.error(f"AI error: {str(exc)}")
        return JSONResponse(
            status_code=exc.status_code, content={"error": str(exc), "type": "AIError"}
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitError):
        logger.warning(f"Rate limit exceeded: {str(exc)}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc), "type": "RateLimitError"},
        )
