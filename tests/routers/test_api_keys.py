"""Tests for the API key routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.routers.api_keys import router
from packages.error_handling.python.error import ResourceNotFoundError as NotFoundError, DatabaseError, AuthenticationError


@pytest.fixture
def client():
    """Create a test client for the API key routes."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_api_key_endpoint():
    """Test creating an API key."""
    # Mock request data
    api_key_data = {
        "name": "Test API Key",
        "expires_in_days": 365
    }

    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock API key
    mock_api_key = {
        "id": "test_api_key_id",
        "name": "Test API Key",
        "api_key": "maily_test_token",
        "created_at": "2023-06-01T00:00:00",
        "expires_at": "2024-06-01T00:00:00",
        "is_active": True
    }

    # Mock create_api_key
    with patch(
        "apps.api.services.api_key_service.create_api_key",
        return_value=mock_api_key
    ) as mock_create_api_key:
        # Import the endpoint function
        from apps.api.routers.api_keys import create_api_key_endpoint

        # Call the function
        result = await create_api_key_endpoint(
            api_key_data=MagicMock(**api_key_data),
            current_user=current_user,
            db=mock_db
        )

        # Assert the result
        assert result == mock_api_key

        # Assert create_api_key was called with the correct parameters
        mock_create_api_key.assert_called_once_with(
            user_id=1,
            name="Test API Key",
            expires_in_days=365,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_create_api_key_endpoint_error():
    """Test creating an API key when an error occurs."""
    # Mock request data
    api_key_data = {
        "name": "Test API Key",
        "expires_in_days": 365
    }

    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock create_api_key to raise an exception
    with patch(
        "apps.api.services.api_key_service.create_api_key",
        side_effect=DatabaseError("Error creating API key")
    ) as mock_create_api_key:
        # Import the endpoint function
        from apps.api.routers.api_keys import create_api_key_endpoint

        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await create_api_key_endpoint(
                api_key_data=MagicMock(**api_key_data),
                current_user=current_user,
                db=mock_db
            )

        # Assert the exception
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Error creating API key"

        # Assert create_api_key was called with the correct parameters
        mock_create_api_key.assert_called_once_with(
            user_id=1,
            name="Test API Key",
            expires_in_days=365,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_list_api_keys_endpoint():
    """Test listing API keys."""
    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock API keys
    mock_api_keys = [
        {
            "id": "test_api_key_id_1",
            "name": "Test API Key 1",
            "created_at": "2023-06-01T00:00:00",
            "expires_at": "2024-06-01T00:00:00",
            "is_active": True,
            "last_used_at": None
        },
        {
            "id": "test_api_key_id_2",
            "name": "Test API Key 2",
            "created_at": "2023-06-01T00:00:00",
            "expires_at": "2024-06-01T00:00:00",
            "is_active": False,
            "last_used_at": "2023-06-02T00:00:00"
        }
    ]

    # Mock list_api_keys
    with patch(
        "apps.api.services.api_key_service.list_api_keys",
        return_value=mock_api_keys
    ) as mock_list_api_keys:
        # Import the endpoint function
        from apps.api.routers.api_keys import list_api_keys_endpoint

        # Call the function
        result = await list_api_keys_endpoint(
            current_user=current_user,
            db=mock_db
        )

        # Assert the result
        assert result == mock_api_keys

        # Assert list_api_keys was called with the correct parameters
        mock_list_api_keys.assert_called_once_with(
            user_id=1,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_list_api_keys_endpoint_error():
    """Test listing API keys when an error occurs."""
    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock list_api_keys to raise an exception
    with patch(
        "apps.api.services.api_key_service.list_api_keys",
        side_effect=DatabaseError("Error listing API keys")
    ) as mock_list_api_keys:
        # Import the endpoint function
        from apps.api.routers.api_keys import list_api_keys_endpoint

        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await list_api_keys_endpoint(
                current_user=current_user,
                db=mock_db
            )

        # Assert the exception
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Error listing API keys"

        # Assert list_api_keys was called with the correct parameters
        mock_list_api_keys.assert_called_once_with(
            user_id=1,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_revoke_api_key_endpoint():
    """Test revoking an API key."""
    # Mock API key ID
    api_key_id = "test_api_key_id"

    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock revoke_api_key
    with patch(
        "apps.api.services.api_key_service.revoke_api_key",
        return_value=None
    ) as mock_revoke_api_key:
        # Import the endpoint function
        from apps.api.routers.api_keys import revoke_api_key_endpoint

        # Call the function
        result = await revoke_api_key_endpoint(
            api_key_id=api_key_id,
            current_user=current_user,
            db=mock_db
        )

        # Assert the result
        assert result == {"message": "API key revoked successfully"}

        # Assert revoke_api_key was called with the correct parameters
        mock_revoke_api_key.assert_called_once_with(
            api_key_id=api_key_id,
            user_id=1,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_revoke_api_key_endpoint_not_found():
    """Test revoking an API key when the API key is not found."""
    # Mock API key ID
    api_key_id = "test_api_key_id"

    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock revoke_api_key to raise an exception
    with patch(
        "apps.api.services.api_key_service.revoke_api_key",
        side_effect=NotFoundError("API key not found")
    ) as mock_revoke_api_key:
        # Import the endpoint function
        from apps.api.routers.api_keys import revoke_api_key_endpoint

        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await revoke_api_key_endpoint(
                api_key_id=api_key_id,
                current_user=current_user,
                db=mock_db
            )

        # Assert the exception
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "API key not found"

        # Assert revoke_api_key was called with the correct parameters
        mock_revoke_api_key.assert_called_once_with(
            api_key_id=api_key_id,
            user_id=1,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_revoke_api_key_endpoint_unauthorized():
    """Test revoking an API key when the user is not authorized."""
    # Mock API key ID
    api_key_id = "test_api_key_id"

    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock revoke_api_key to raise an exception
    with patch(
        "apps.api.services.api_key_service.revoke_api_key",
        side_effect=AuthenticationError("You do not have permission to revoke this API key")
    ) as mock_revoke_api_key:
        # Import the endpoint function
        from apps.api.routers.api_keys import revoke_api_key_endpoint

        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await revoke_api_key_endpoint(
                api_key_id=api_key_id,
                current_user=current_user,
                db=mock_db
            )

        # Assert the exception
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You do not have permission to revoke this API key"

        # Assert revoke_api_key was called with the correct parameters
        mock_revoke_api_key.assert_called_once_with(
            api_key_id=api_key_id,
            user_id=1,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_revoke_api_key_endpoint_database_error():
    """Test revoking an API key when a database error occurs."""
    # Mock API key ID
    api_key_id = "test_api_key_id"

    # Mock current user
    current_user = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }

    # Mock database session
    mock_db = AsyncMock()

    # Mock revoke_api_key to raise an exception
    with patch(
        "apps.api.services.api_key_service.revoke_api_key",
        side_effect=DatabaseError("Error revoking API key")
    ) as mock_revoke_api_key:
        # Import the endpoint function
        from apps.api.routers.api_keys import revoke_api_key_endpoint

        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await revoke_api_key_endpoint(
                api_key_id=api_key_id,
                current_user=current_user,
                db=mock_db
            )

        # Assert the exception
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Error revoking API key"

        # Assert revoke_api_key was called with the correct parameters
        mock_revoke_api_key.assert_called_once_with(
            api_key_id=api_key_id,
            user_id=1,
            db=mock_db
        )
