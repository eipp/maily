"""Main FastAPI application with standardized authentication and security."""
import logging
import os
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from middleware.auth_setup import setup_auth_middleware
from middleware.standardized_auth import require_auth, require_admin, optional_auth
from middleware.owasp_middleware import setup_owasp_middleware
from services.api_key_service import create_api_key, revoke_api_key, list_api_keys, has_scope
from services.vault_service import vault_service
from services.service_auth_client import service_auth_client
from errors.exceptions import AuthenticationError, NotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maily-api")

# Create FastAPI app
app = FastAPI(
    title="Maily API",
    description="API for Maily email management platform",
    version="1.0.0",
)

# Set up middleware
setup_auth_middleware(app)
setup_owasp_middleware(
    app,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
    allowed_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    csp_directives={
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https://cdn.maily.com"],
        "connect-src": ["'self'", "https://*.maily.com"],
        "font-src": ["'self'", "data:"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"]
    }
)

# Register error handlers
@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"error": str(exc), "code": "unauthorized"}
    )

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": str(exc), "code": "not_found"}
    )


# Define API models
class ApiKeyCreate(BaseModel):
    name: str
    scopes: Optional[List[str]] = None
    expires_in_days: Optional[int] = 90


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    api_key: Optional[str] = None
    scopes: List[str]
    created_at: str
    expires_at: str
    is_active: bool


# Public endpoints
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/public-info")
async def public_info():
    """Public information endpoint."""
    return {
        "name": "Maily API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


# Authenticated endpoints
@app.get("/api/user/me")
async def get_current_user(user: Dict[str, Any] = Depends(require_auth)):
    """Get the current user information."""
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "auth_method": user.get("auth_method", "jwt")
    }


# API key management endpoints
@app.post("/api/api-keys", response_model=ApiKeyResponse)
async def create_api_key_handler(
    api_key_data: ApiKeyCreate,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a new API key."""
    api_key = await create_api_key(
        user_id=user["id"],
        name=api_key_data.name,
        scopes=api_key_data.scopes,
        expires_in_days=api_key_data.expires_in_days
    )

    return api_key


@app.get("/api/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys_handler(user: Dict[str, Any] = Depends(require_auth)):
    """List all API keys for the current user."""
    api_keys = await list_api_keys(user["id"])
    return api_keys


@app.delete("/api/api-keys/{api_key_id}")
async def revoke_api_key_handler(
    api_key_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Revoke an API key."""
    await revoke_api_key(api_key_id, user["id"])
    return {"status": "success", "message": "API key revoked"}


# Admin-only endpoints
@app.get("/api/admin/users")
async def list_users(user: Dict[str, Any] = Depends(require_admin)):
    """List all users (admin only)."""
    # This is just a placeholder - in a real application, you would fetch users from the database
    return [
        {"id": "1", "email": "admin@example.com", "name": "Admin User", "is_admin": True},
        {"id": "2", "email": "user@example.com", "name": "Regular User", "is_admin": False}
    ]


# Vault integration example
@app.get("/api/admin/secrets")
async def list_secrets(
    path: str = "kv/data",
    user: Dict[str, Any] = Depends(require_admin)
):
    """List secrets (admin only)."""
    try:
        secrets = await vault_service.list_secrets(path)
        return {"secrets": secrets}
    except Exception as e:
        logger.error(f"Error listing secrets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list secrets")


# Service-to-service authentication example
@app.get("/api/services/info")
async def get_service_info(user: Dict[str, Any] = Depends(require_auth)):
    """Get information about available services."""
    # Check if this is a service-to-service request
    if user.get("auth_method") == "service_token":
        return {
            "service_name": user.get("service_name"),
            "permissions": user.get("permissions", []),
            "available_services": [
                {"name": "email-service", "url": "http://email-service/api/v1"},
                {"name": "user-service", "url": "http://user-service/api/v1"},
                {"name": "analytics-service", "url": "http://analytics-service/api/v1"}
            ]
        }

    # Otherwise, return a subset of information for regular users
    return {
        "available_services": [
            {"name": "email-service", "description": "Email sending and management"},
            {"name": "user-service", "description": "User account management"},
            {"name": "analytics-service", "description": "Email analytics and reporting"}
        ]
    }


# Optional authentication example
@app.get("/api/content")
async def get_content(user: Optional[Dict[str, Any]] = Depends(optional_auth)):
    """Get content, with additional information for authenticated users."""
    content = {
        "title": "Welcome to Maily",
        "description": "Email management platform",
        "public_features": [
            "Intuitive email editor",
            "Template management",
            "Basic analytics"
        ]
    }

    # If the user is authenticated, add additional information
    if user:
        content["user"] = {
            "id": user.get("id"),
            "name": user.get("name")
        }
        content["premium_features"] = [
            "Advanced analytics",
            "A/B testing",
            "Email automation"
        ]

    return content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
