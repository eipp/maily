"""Tests for the authentication middleware."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from apps.api.middleware.auth_middleware import (
    get_current_user,
    _authenticate_with_jwt,
    _authenticate_with_api_key,
    require_admin,
    optional_auth
)


@pytest.mark.asyncio
async def test_get_current_user_jwt():
    """Test getting the current user with a JWT token."""
    # Mock credentials
    mock_credentials = MagicMock()
    mock_credentials.credentials = "jwt_token"

    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    mock_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False,
        "auth0_id": "auth0|123456789"
    }

    # Mock _authenticate_with_jwt
    with patch(
        "apps.api.middleware.auth_middleware._authenticate_with_jwt",
        return_value=mock_user
    ) as mock_jwt_auth:
        # Call the function
        result = await get_current_user(mock_credentials, mock_db)

        # Assert the result
        assert result == mock_user

        # Assert _authenticate_with_jwt was called with the correct parameters
        mock_jwt_auth.assert_called_once_with("jwt_token", mock_db)


@pytest.mark.asyncio
async def test_get_current_user_api_key():
    """Test getting the current user with an API key."""
    # Mock credentials
    mock_credentials = MagicMock()
    mock_credentials.credentials = "api_key"

    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    mock_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False,
        "auth_method": "api_key"
    }

    # Mock _authenticate_with_jwt to raise an exception
    with patch(
        "apps.api.middleware.auth_middleware._authenticate_with_jwt",
        side_effect=HTTPException(status_code=401, detail="Invalid token")
    ) as mock_jwt_auth:
        # Mock _authenticate_with_api_key
        with patch(
            "apps.api.middleware.auth_middleware._authenticate_with_api_key",
            return_value=mock_user
        ) as mock_api_key_auth:
            # Call the function
            result = await get_current_user(mock_credentials, mock_db)

            # Assert the result
            assert result == mock_user

            # Assert _authenticate_with_jwt was called with the correct parameters
            mock_jwt_auth.assert_called_once_with("api_key", mock_db)

            # Assert _authenticate_with_api_key was called with the correct parameters
            mock_api_key_auth.assert_called_once_with("api_key", mock_db)


@pytest.mark.asyncio
async def test_get_current_user_both_fail():
    """Test getting the current user when both authentication methods fail."""
    # Mock credentials
    mock_credentials = MagicMock()
    mock_credentials.credentials = "invalid_token"

    # Mock database session
    mock_db = AsyncMock()

    # Mock _authenticate_with_jwt to raise an exception
    with patch(
        "apps.api.middleware.auth_middleware._authenticate_with_jwt",
        side_effect=HTTPException(status_code=401, detail="Invalid token")
    ) as mock_jwt_auth:
        # Mock _authenticate_with_api_key to raise an exception
        with patch(
            "apps.api.middleware.auth_middleware._authenticate_with_api_key",
            side_effect=HTTPException(status_code=401, detail="Invalid API key")
        ) as mock_api_key_auth:
            # Call the function
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)

            # Assert the exception
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid token"

            # Assert _authenticate_with_jwt was called with the correct parameters
            mock_jwt_auth.assert_called_once_with("invalid_token", mock_db)

            # Assert _authenticate_with_api_key was called with the correct parameters
            mock_api_key_auth.assert_called_once_with("invalid_token", mock_db)


@pytest.mark.asyncio
async def test_authenticate_with_jwt():
    """Test authenticating with a JWT token."""
    # Mock token
    token = "jwt_token"

    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.is_admin = False

    # Mock payload
    mock_payload = {
        "sub": "auth0|123456789",
        "email": "test@example.com",
        "name": "Test User"
    }

    # Mock PyJWKClient
    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = "signing_key"
    mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

    # Mock jwt.decode
    with patch("jose.jwt.decode", return_value=mock_payload):
        # Mock PyJWKClient
        with patch("jose.jwt.PyJWKClient", return_value=mock_jwks_client):
            # Mock get_user_by_auth0_id
            with patch(
                "apps.api.services.user_service.get_user_by_auth0_id",
                return_value=mock_user
            ) as mock_get_user:
                # Mock environment variables
                with patch("os.getenv") as mock_getenv:
                    mock_getenv.side_effect = lambda key, default=None: {
                        "AUTH0_DOMAIN": "test.auth0.com",
                        "AUTH0_AUDIENCE": "test_audience"
                    }.get(key, default)

                    # Call the function
                    result = await _authenticate_with_jwt(token, mock_db)

                    # Assert the result
                    assert result["id"] == 1
                    assert result["email"] == "test@example.com"
                    assert result["name"] == "Test User"
                    assert result["is_admin"] is False
                    assert result["auth0_id"] == "auth0|123456789"

                    # Assert get_user_by_auth0_id was called with the correct parameters
                    mock_get_user.assert_called_once_with("auth0|123456789", mock_db)


@pytest.mark.asyncio
async def test_authenticate_with_api_key():
    """Test authenticating with an API key."""
    # Mock API key
    api_key = "api_key"

    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.is_admin = False

    # Mock get_user_by_api_key
    with patch(
        "apps.api.services.api_key_service.get_user_by_api_key",
        return_value=mock_user
    ) as mock_get_user:
        # Call the function
        result = await _authenticate_with_api_key(api_key, mock_db)

        # Assert the result
        assert result["id"] == 1
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert result["is_admin"] is False
        assert result["auth_method"] == "api_key"

        # Assert get_user_by_api_key was called with the correct parameters
        mock_get_user.assert_called_once_with(api_key, mock_db)


@pytest.mark.asyncio
async def test_authenticate_with_api_key_not_found():
    """Test authenticating with an API key when the user is not found."""
    # Mock API key
    api_key = "api_key"

    # Mock database session
    mock_db = AsyncMock()

    # Mock get_user_by_api_key
    with patch(
        "apps.api.services.api_key_service.get_user_by_api_key",
        return_value=None
    ) as mock_get_user:
        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await _authenticate_with_api_key(api_key, mock_db)

        # Assert the exception
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authentication credentials"

        # Assert get_user_by_api_key was called with the correct parameters
        mock_get_user.assert_called_once_with(api_key, mock_db)


def test_require_admin():
    """Test requiring admin privileges."""
    # Mock user
    mock_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": True
    }

    # Call the function
    result = require_admin(mock_user)

    # Assert the result
    assert result == mock_user


def test_require_admin_not_admin():
    """Test requiring admin privileges when the user is not an admin."""
    # Mock user
    mock_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Call the function
    with pytest.raises(HTTPException) as exc_info:
        require_admin(mock_user)

    # Assert the exception
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin privileges required"


@pytest.mark.asyncio
async def test_optional_auth():
    """Test optional authentication."""
    # Mock request
    mock_request = MagicMock()
    mock_request.headers = {"Authorization": "Bearer token"}

    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    mock_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock _authenticate_with_jwt
    with patch(
        "apps.api.middleware.auth_middleware._authenticate_with_jwt",
        return_value=mock_user
    ) as mock_jwt_auth:
        # Call the function
        result = await optional_auth(mock_request, mock_db)

        # Assert the result
        assert result == mock_user

        # Assert _authenticate_with_jwt was called with the correct parameters
        mock_jwt_auth.assert_called_once_with("token", mock_db)


@pytest.mark.asyncio
async def test_optional_auth_no_header():
    """Test optional authentication when there is no Authorization header."""
    # Mock request
    mock_request = MagicMock()
    mock_request.headers = {}

    # Mock database session
    mock_db = AsyncMock()

    # Call the function
    result = await optional_auth(mock_request, mock_db)

    # Assert the result
    assert result is None


@pytest.mark.asyncio
async def test_optional_auth_invalid_scheme():
    """Test optional authentication when the Authorization scheme is invalid."""
    # Mock request
    mock_request = MagicMock()
    mock_request.headers = {"Authorization": "Basic token"}

    # Mock database session
    mock_db = AsyncMock()

    # Call the function
    result = await optional_auth(mock_request, mock_db)

    # Assert the result
    assert result is None


@pytest.mark.asyncio
async def test_optional_auth_both_fail():
    """Test optional authentication when both authentication methods fail."""
    # Mock request
    mock_request = MagicMock()
    mock_request.headers = {"Authorization": "Bearer token"}

    # Mock database session
    mock_db = AsyncMock()

    # Mock _authenticate_with_jwt to raise an exception
    with patch(
        "apps.api.middleware.auth_middleware._authenticate_with_jwt",
        side_effect=HTTPException(status_code=401, detail="Invalid token")
    ) as mock_jwt_auth:
        # Mock _authenticate_with_api_key to raise an exception
        with patch(
            "apps.api.middleware.auth_middleware._authenticate_with_api_key",
            side_effect=HTTPException(status_code=401, detail="Invalid API key")
        ) as mock_api_key_auth:
            # Call the function
            result = await optional_auth(mock_request, mock_db)

            # Assert the result
            assert result is None

            # Assert _authenticate_with_jwt was called with the correct parameters
            mock_jwt_auth.assert_called_once_with("token", mock_db)

            # Assert _authenticate_with_api_key was called with the correct parameters
            mock_api_key_auth.assert_called_once_with("token", mock_db)
