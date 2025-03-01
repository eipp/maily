"""JWT Authentication Provider implementation using Auth0."""
import logging
import os
from typing import Dict, Any, Optional

from jose import jwt, JWTError, jwk
import httpx

from ..standardized_auth import JWTProvider, JWTVerificationError
from database.session import get_db
from services.user_service import get_user_by_auth0_id, create_user_from_auth0

logger = logging.getLogger(__name__)

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_ALGORITHMS = ["RS256"]


class Auth0JWTProvider(JWTProvider):
    """Auth0 JWT authentication provider."""

    def __init__(self):
        """Initialize the Auth0 JWT provider."""
        if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
            logger.error("Auth0 configuration is missing")
            raise ValueError("Auth0 configuration is missing")

        self.domain = AUTH0_DOMAIN
        self.audience = AUTH0_AUDIENCE
        self.algorithms = AUTH0_ALGORITHMS
        self.jwks_client = None

    async def _get_jwks_client(self):
        """Get or create a JWKS client."""
        if not self.jwks_client:
            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(jwks_url)
                    response.raise_for_status()
                    jwks = response.json()
                    self.jwks_client = jwk.PyJWKClient(jwks_url, jwks_cache=jwks)
            except Exception as e:
                logger.error(f"Failed to initialize JWKS client: {str(e)}")
                raise JWTVerificationError(f"Failed to initialize JWKS client: {str(e)}")
        return self.jwks_client

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify an Auth0 JWT token and return user information.

        Args:
            token: The JWT token to verify.

        Returns:
            User information if the token is valid.

        Raises:
            JWTVerificationError: If token verification fails.
        """
        try:
            # Verify and decode the JWT
            jwks_client = await self._get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )

            # Extract user information from the token
            auth0_id = payload.get("sub")
            if not auth0_id:
                raise JWTVerificationError("Invalid token: missing subject")

            # Get or create user in database
            async with get_db() as db:
                user = await get_user_by_auth0_id(auth0_id, db)

                if not user:
                    # Extract user information from the token
                    email = payload.get("email")
                    name = payload.get("name")

                    if not email:
                        raise JWTVerificationError("Invalid token: missing email")

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
                "auth0_id": auth0_id,
                "auth_method": "jwt"
            }
        except JWTError as e:
            logger.error(f"JWT authentication error: {str(e)}")
            raise JWTVerificationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise JWTVerificationError(f"Authentication error: {str(e)}")
