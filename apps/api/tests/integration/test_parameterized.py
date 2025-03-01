"""Parameterized integration tests for API authentication.

This module contains parameterized tests to validate both JWT and API key authentication.
"""
import pytest
from fastapi.testclient import TestClient
import pytest_asyncio
import os
import json
from unittest.mock import patch

# Explicitly adding the current directory to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import API modules
from apps.api.main_fixed import app  # Using main_fixed instead of main as it appears to be more complete
from apps.api.config.api_keys import API_KEYS


@pytest.fixture
def test_client():
    """Create a test client for the application."""
    return TestClient(app)


@pytest.mark.parametrize(
    "auth_header,header_value,expected_status,description",
    [
        # JWT token tests
        (
            "Authorization",
            "Bearer valid_token",
            200,
            "Valid JWT token should succeed",
        ),
        (
            "Authorization",
            "Bearer invalid_token",
            403,
            "Invalid JWT token should fail with 403",
        ),
        (
            "Authorization",
            "invalid_format",
            403,
            "Invalid auth header format should fail",
        ),
        # API key tests
        (
            "X-API-Key",
            "test_api_key",
            200,
            "Valid API key should succeed",
        ),
        (
            "X-API-Key",
            "invalid_api_key",
            401,
            "Invalid API key should fail with 401",
        ),
        # No authentication
        (
            None,
            None,
            403,
            "No authentication should fail with 403",
        ),
    ],
)
def test_authentication_methods(
    test_client, auth_header, header_value, expected_status, description
):
    """Test different authentication methods.

    Args:
        test_client: The test client.
        auth_header: The authentication header name.
        header_value: The authentication header value.
        expected_status: The expected HTTP status code.
        description: A description of the test case.
    """
    # Setup headers
    headers = {}
    if auth_header and header_value:
        headers[auth_header] = header_value

    # Mock JWT verification to avoid actual Auth0 calls
    with patch('apps.api.middleware.auth0.Auth0JWTBearer._verify_jwt') as mock_verify:
        # Configure mock to succeed for valid token, fail for others
        if header_value == "Bearer valid_token":
            mock_verify.return_value = {"sub": "user|123", "permissions": ["read:data"]}
        else:
            mock_verify.side_effect = Exception("Invalid token")

        # Make request to a protected endpoint
        response = test_client.get("/api/v1/user/me", headers=headers)

        # Assert the expected status code
        assert response.status_code == expected_status, description

        # For successful responses, check the payload
        if expected_status == 200:
            if auth_header == "Authorization":
                assert response.json().get("sub") == "user|123"
            elif auth_header == "X-API-Key":
                assert response.json().get("sub") == "system|api_key"


@pytest.mark.parametrize(
    "api_key,user_type,expected_permissions",
    [
        (
            "test_api_key",
            "system",
            ["read", "write"],
        ),
    ],
)
def test_api_key_permissions(test_client, api_key, user_type, expected_permissions):
    """Test API key permissions.

    Args:
        test_client: The test client.
        api_key: The API key to test.
        user_type: The expected user type.
        expected_permissions: The expected permissions.
    """
    # Setup headers with API key
    headers = {"X-API-Key": api_key}

    # Make request to permissions endpoint
    response = test_client.get("/api/v1/user/permissions", headers=headers)

    # Assert successful response
    assert response.status_code == 200

    # Verify response data
    data = response.json()
    assert data.get("user_type") == user_type

    # Check that all expected permissions are present
    for permission in expected_permissions:
        assert permission in data.get("permissions")
