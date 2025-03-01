"""
Authentication and authorization configuration for the API.
"""

import os
from typing import Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "maily.us.auth0.com")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "https://api.maily.com")
AUTH0_ALGORITHMS = ["RS256"]
AUTH0_ISSUER = f"https://{AUTH0_DOMAIN}/"

# JWKS client for verifying JWT signatures
class JWKSClient:
    def __init__(self, domain: str):
        self.domain = domain
        self.jwks_uri = f"https://{domain}/.well-known/jwks.json"
        self.jwks: Optional[Dict] = None

    async def get_jwks(self) -> Dict:
        """Fetch the JWKS from Auth0."""
        if self.jwks is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri)
                response.raise_for_status()
                self.jwks = response.json()
        return self.jwks

    async def get_signing_key(self, kid: str) -> Dict:
        """Get the signing key from the JWKS."""
        jwks = await self.get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate key",
        )

jwks_client = JWKSClient(AUTH0_DOMAIN)

# Security scheme for JWT authentication
security = HTTPBearer()

# Role-based access control
class RBACMiddleware:
    """Middleware for role-based access control."""

    def __init__(self, required_roles: Optional[List[str]] = None):
        self.required_roles = required_roles or []

    async def __call__(self, request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Validate the JWT and check if the user has the required roles."""
        try:
            token = credentials.credentials
            header = jwt.get_unverified_header(token)
            key = await jwks_client.get_signing_key(header["kid"])

            payload = jwt.decode(
                token,
                key,
                algorithms=AUTH0_ALGORITHMS,
                audience=AUTH0_API_AUDIENCE,
                issuer=AUTH0_ISSUER,
            )

            # Check if the user has the required roles
            if self.required_roles:
                user_roles = payload.get("permissions", [])
                if not any(role in user_roles for role in self.required_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )

            # Add the user information to the request state
            request.state.user = payload
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

# Dependency for requiring authentication
def require_auth():
    """Dependency for requiring authentication."""
    return RBACMiddleware()

# Dependency for requiring specific roles
def require_roles(roles: Union[str, List[str]]):
    """Dependency for requiring specific roles."""
    if isinstance(roles, str):
        roles = [roles]
    return RBACMiddleware(required_roles=roles)

# Permission constants
class Permissions:
    """Permission constants for role-based access control."""

    # User permissions
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"

    # Campaign permissions
    READ_CAMPAIGNS = "read:campaigns"
    WRITE_CAMPAIGNS = "write:campaigns"

    # Email permissions
    READ_EMAILS = "read:emails"
    WRITE_EMAILS = "write:emails"
    SEND_EMAILS = "send:emails"

    # Analytics permissions
    READ_ANALYTICS = "read:analytics"

    # Admin permissions
    ADMIN = "admin"

    # Role mappings
    ROLES = {
        "user": [READ_CAMPAIGNS, READ_EMAILS, SEND_EMAILS, READ_ANALYTICS],
        "editor": [READ_CAMPAIGNS, WRITE_CAMPAIGNS, READ_EMAILS, WRITE_EMAILS, SEND_EMAILS, READ_ANALYTICS],
        "admin": [READ_USERS, WRITE_USERS, READ_CAMPAIGNS, WRITE_CAMPAIGNS, READ_EMAILS, WRITE_EMAILS, SEND_EMAILS, READ_ANALYTICS, ADMIN],
    }
