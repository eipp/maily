"""API Key Authentication Provider implementation."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..standardized_auth import APIKeyProvider, APIKeyVerificationError
from database.session import get_db
from services.api_key_service import get_user_by_api_key, update_api_key_last_used

logger = logging.getLogger(__name__)


class DatabaseAPIKeyProvider(APIKeyProvider):
    """Database-backed API key authentication provider."""

    async def verify_key(self, api_key: str) -> Dict[str, Any]:
        """Verify an API key and return user information.

        Args:
            api_key: The API key to verify.

        Returns:
            User information if the key is valid.

        Raises:
            APIKeyVerificationError: If key verification fails.
        """
        try:
            # Check API key format
            if not api_key.startswith("mil_"):
                raise APIKeyVerificationError("Invalid API key format")

            # Get the user from the database
            async with get_db() as db:
                user, api_key_obj = await get_user_by_api_key(api_key, db, return_api_key=True)

                if not user:
                    raise APIKeyVerificationError("Invalid API key")

                # Check if the API key has the required scopes for the request
                # This will be implemented when handling scopes in the request

                # Update last used timestamp
                await update_api_key_last_used(api_key_obj.id, db)

                # Return the user information
                return {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "is_admin": user.is_admin,
                    "auth_method": "api_key",
                    "api_key_id": api_key_obj.id,
                    "api_key_scopes": api_key_obj.scopes if hasattr(api_key_obj, "scopes") else []
                }
        except APIKeyVerificationError:
            raise
        except Exception as e:
            logger.error(f"API key verification error: {str(e)}")
            raise APIKeyVerificationError(f"API key verification error: {str(e)}")
