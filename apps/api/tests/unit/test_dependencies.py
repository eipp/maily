import pytest
from fastapi import HTTPException

from ....dependencies import get_current_user, get_model_service, get_redis
from ....errors import AuthenticationError
from ....models import MODEL_REGISTRY


def test_get_model_service_valid():
    """Test getting a valid model service."""
    for model_name in MODEL_REGISTRY.keys():
        service = get_model_service(model_name)
        assert service == MODEL_REGISTRY[model_name]


def test_get_model_service_invalid():
    """Test getting an invalid model service."""
    with pytest.raises(HTTPException) as exc_info:
        get_model_service("invalid_model")
    assert exc_info.value.status_code == 400
    assert "not supported" in str(exc_info.value.detail)


def test_get_redis_unavailable(monkeypatch):
    """Test Redis dependency when service is unavailable."""
    monkeypatch.setattr("backend.dependencies.redis_client", None)
    with pytest.raises(HTTPException) as exc_info:
        get_redis()
    assert exc_info.value.status_code == 503
    assert "Redis service unavailable" in str(exc_info.value.detail)


def test_get_current_user_valid(monkeypatch):
    """Test user authentication with valid API key."""
    monkeypatch.setattr("backend.dependencies.settings.API_KEY", "test-api-key")
    user = get_current_user("test-api-key")
    assert user == {"user_id": 1}


def test_get_current_user_invalid():
    """Test user authentication with invalid API key."""
    with pytest.raises(AuthenticationError) as exc_info:
        get_current_user("invalid-api-key")
    assert "Invalid API key" in str(exc_info.value)
