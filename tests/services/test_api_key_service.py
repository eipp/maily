"""Tests for the API key service."""
import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.services.api_key_service import (
    get_user_by_api_key,
    create_api_key,
    revoke_api_key,
    list_api_keys
)
from apps.api.errors.exceptions import NotFoundError, AuthenticationError


@pytest.mark.asyncio
async def test_get_user_by_api_key():
    """Test getting a user by API key."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock API key
    api_key = "maily_test_api_key"
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

    # Mock API key object
    mock_api_key = MagicMock()
    mock_api_key.user_id = 1

    # Mock user object
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"

    # Mock database query results
    mock_api_key_result = AsyncMock()
    mock_api_key_result.scalars.return_value.first.return_value = mock_api_key

    mock_user_result = AsyncMock()
    mock_user_result.scalars.return_value.first.return_value = mock_user

    # Mock database execute method
    mock_db.execute.side_effect = [mock_api_key_result, mock_user_result]

    # Call the function
    result = await get_user_by_api_key(api_key, mock_db)

    # Assert the result
    assert result == mock_user

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 2

    # Check that the hashed key was used in the query
    args, kwargs = mock_db.execute.call_args_list[0]
    assert hashed_key in str(args[0])


@pytest.mark.asyncio
async def test_get_user_by_api_key_not_found():
    """Test getting a user by API key when the API key is not found."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock API key
    api_key = "maily_test_api_key"

    # Mock database query results
    mock_api_key_result = AsyncMock()
    mock_api_key_result.scalars.return_value.first.return_value = None

    # Mock database execute method
    mock_db.execute.return_value = mock_api_key_result

    # Call the function
    result = await get_user_by_api_key(api_key, mock_db)

    # Assert the result
    assert result is None

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1


@pytest.mark.asyncio
async def test_create_api_key():
    """Test creating an API key."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    user_id = 1
    mock_user = MagicMock()
    mock_user.id = user_id

    # Mock database query results
    mock_user_result = AsyncMock()
    mock_user_result.scalars.return_value.first.return_value = mock_user

    # Mock database execute method
    mock_db.execute.return_value = mock_user_result

    # Call the function
    with patch("secrets.token_urlsafe", return_value="test_token"):
        result = await create_api_key(user_id, "Test API Key", 365, mock_db)

    # Assert the result
    assert result["name"] == "Test API Key"
    assert result["api_key"] == "maily_test_token"
    assert result["is_active"] is True

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1
    assert mock_db.add.call_count == 1
    assert mock_db.commit.call_count == 1
    assert mock_db.refresh.call_count == 1


@pytest.mark.asyncio
async def test_create_api_key_user_not_found():
    """Test creating an API key when the user is not found."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    user_id = 1

    # Mock database query results
    mock_user_result = AsyncMock()
    mock_user_result.scalars.return_value.first.return_value = None

    # Mock database execute method
    mock_db.execute.return_value = mock_user_result

    # Call the function
    with pytest.raises(NotFoundError):
        await create_api_key(user_id, "Test API Key", 365, mock_db)

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1
    assert mock_db.add.call_count == 0
    assert mock_db.commit.call_count == 0
    assert mock_db.refresh.call_count == 0


@pytest.mark.asyncio
async def test_revoke_api_key():
    """Test revoking an API key."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock API key
    api_key_id = "test_api_key_id"
    user_id = 1

    # Mock API key object
    mock_api_key = MagicMock()
    mock_api_key.id = api_key_id
    mock_api_key.user_id = user_id

    # Mock database query results
    mock_api_key_result = AsyncMock()
    mock_api_key_result.scalars.return_value.first.return_value = mock_api_key

    # Mock database execute method
    mock_db.execute.return_value = mock_api_key_result

    # Call the function
    await revoke_api_key(api_key_id, user_id, mock_db)

    # Assert the API key was revoked
    assert mock_api_key.is_active is False

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 1


@pytest.mark.asyncio
async def test_revoke_api_key_not_found():
    """Test revoking an API key when the API key is not found."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock API key
    api_key_id = "test_api_key_id"
    user_id = 1

    # Mock database query results
    mock_api_key_result = AsyncMock()
    mock_api_key_result.scalars.return_value.first.return_value = None

    # Mock database execute method
    mock_db.execute.return_value = mock_api_key_result

    # Call the function
    with pytest.raises(NotFoundError):
        await revoke_api_key(api_key_id, user_id, mock_db)

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 0


@pytest.mark.asyncio
async def test_revoke_api_key_unauthorized():
    """Test revoking an API key when the user is not authorized."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock API key
    api_key_id = "test_api_key_id"
    user_id = 1

    # Mock API key object
    mock_api_key = MagicMock()
    mock_api_key.id = api_key_id
    mock_api_key.user_id = 2  # Different user ID

    # Mock database query results
    mock_api_key_result = AsyncMock()
    mock_api_key_result.scalars.return_value.first.return_value = mock_api_key

    # Mock database execute method
    mock_db.execute.return_value = mock_api_key_result

    # Call the function
    with pytest.raises(AuthenticationError):
        await revoke_api_key(api_key_id, user_id, mock_db)

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 0


@pytest.mark.asyncio
async def test_list_api_keys():
    """Test listing API keys."""
    # Mock database session
    mock_db = AsyncMock()

    # Mock user
    user_id = 1

    # Mock API key objects
    mock_api_key1 = MagicMock()
    mock_api_key1.id = "test_api_key_id_1"
    mock_api_key1.name = "Test API Key 1"
    mock_api_key1.created_at = datetime.utcnow()
    mock_api_key1.expires_at = datetime.utcnow() + timedelta(days=365)
    mock_api_key1.is_active = True
    mock_api_key1.last_used_at = None

    mock_api_key2 = MagicMock()
    mock_api_key2.id = "test_api_key_id_2"
    mock_api_key2.name = "Test API Key 2"
    mock_api_key2.created_at = datetime.utcnow()
    mock_api_key2.expires_at = datetime.utcnow() + timedelta(days=365)
    mock_api_key2.is_active = False
    mock_api_key2.last_used_at = datetime.utcnow()

    # Mock database query results
    mock_api_keys_result = AsyncMock()
    mock_api_keys_result.scalars.return_value.all.return_value = [mock_api_key1, mock_api_key2]

    # Mock database execute method
    mock_db.execute.return_value = mock_api_keys_result

    # Call the function
    result = await list_api_keys(user_id, mock_db)

    # Assert the result
    assert len(result) == 2
    assert result[0]["id"] == "test_api_key_id_1"
    assert result[0]["name"] == "Test API Key 1"
    assert result[0]["is_active"] is True
    assert result[0]["last_used_at"] is None

    assert result[1]["id"] == "test_api_key_id_2"
    assert result[1]["name"] == "Test API Key 2"
    assert result[1]["is_active"] is False
    assert result[1]["last_used_at"] is not None

    # Assert the database was called with the correct parameters
    assert mock_db.execute.call_count == 1
