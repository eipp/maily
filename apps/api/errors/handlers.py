from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from .exceptions import MailyError


async def maily_error_handler(request: Request, exc: MailyError):
    """Handle Maily-specific errors."""
    logger.error(f"Error processing request: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message}},
    )


async def general_error_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
