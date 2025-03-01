"""Test API key authentication functionality."""
import pytest
from unittest.mock import patch, MagicMock

from apps.api.middleware.auth0 import Auth0JWTBearer, get_user_from_api_key
from apps.api.config.api_keys import validate_api_key


def test_api_key_validation():
    """Test API key validation logic."""
    # Test with valid API key
    with patch('apps.api.config.api_keys.API_KEYS', {"test_key": {}}):
        assert validate_api_key("test_key") is True
        assert validate_api_key("invalid_key") is False


def test_get_user_from_api_key():
    """Test fetching user from API key."""
    user_info = get_user_from_api_key("test_key")
    assert user_info["id"] == "system"
    assert "roles" in user_info


@pytest.mark.asyncio
async def test_auth0_jwt_bearer_with_api_key():
    """Test Auth0JWTBearer middleware with API key."""
    # Create mock request with API key
    mock_request = MagicMock()
    mock_request.headers = {"X-API-Key": "test_key"}

    # Create Auth0JWTBearer instance
    auth = Auth0JWTBearer()

    # Mock validate_api_key to return True
    with patch('apps.api.config.api_keys.validate_api_key', return_value=True):
        # Call __call__ method
        result = await auth.__call__(mock_request)

        # Check result
        assert result == {"sub": "system|api_key"}
        assert mock_request.state.auth_type == "api_key"
        assert mock_request.state.user is not None


@pytest.mark.asyncio
async def test_auth0_jwt_bearer_with_invalid_api_key():
    """Test Auth0JWTBearer middleware with invalid API key."""
    # Create mock request with invalid API key
    mock_request = MagicMock()
    mock_request.headers = {"X-API-Key": "invalid_key"}

    # Create Auth0JWTBearer instance
    auth = Auth0JWTBearer()

    # Mock validate_api_key to return False
    with patch('apps.api.config.api_keys.validate_api_key', return_value=False):
        # Call __call__ method should raise HTTPException
        with pytest.raises(Exception) as excinfo:
            await auth.__call__(mock_request)

        # Check exception
        assert "401" in str(excinfo.value)  # Status code 401
        assert "Invalid API key" in str(excinfo.value)  # Error message
