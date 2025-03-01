import pytest
from fastapi import Request

from ....errors import (
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    MailyError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    general_error_handler,
    maily_error_handler,
)


@pytest.fixture
def mock_request():
    """Mock FastAPI request."""
    return Request({"type": "http", "method": "GET", "url": "http://test"})


async def test_maily_error_handler(mock_request):
    """Test handling of Maily-specific errors."""
    errors = [
        (DatabaseError("DB connection failed"), 503),
        (AuthenticationError("Invalid token"), 401),
        (RateLimitError("Too many requests"), 429),
        (ValidationError("Invalid input"), 400),
        (NotFoundError("Resource not found"), 404),
        (ConfigurationError("Invalid config"), 500),
    ]

    for error, expected_status in errors:
        response = await maily_error_handler(mock_request, error)
        assert response.status_code == expected_status
        data = response.body.decode()
        assert error.message in data
        assert error.error_code in data


async def test_general_error_handler(mock_request):
    """Test handling of unhandled exceptions."""
    error = Exception("Unexpected error")
    response = await general_error_handler(mock_request, error)
    assert response.status_code == 500
    data = response.body.decode()
    assert "INTERNAL_ERROR" in data
    assert "unexpected error" in data.lower()


async def test_error_response_format(mock_request):
    """Test error response format."""
    error = ValidationError("Test error")
    response = await maily_error_handler(mock_request, error)
    data = response.body.decode()
    assert '"error"' in data
    assert '"code"' in data
    assert '"message"' in data
