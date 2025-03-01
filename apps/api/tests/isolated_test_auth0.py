"""Isolated test for Auth0JWTBearer middleware."""
import sys
import os
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path for imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create mock modules to avoid import errors
sys.modules['config.settings'] = MagicMock()
sys.modules['config.auth0'] = MagicMock()
sys.modules['config.auth0.auth0_settings'] = MagicMock()
sys.modules['config.auth0.auth0_settings.DOMAIN'] = MagicMock(return_value='example.auth0.com')
sys.modules['config.auth0.auth0_settings.API_AUDIENCE'] = MagicMock(return_value='api')

# Import the auth0 middleware with mocked dependencies
from apps.api.middleware.auth0 import Auth0JWTBearer, get_user_from_api_key

# Create a standalone API key validation function
def validate_api_key(api_key):
    """Mock API key validation.

    Args:
        api_key: The API key to validate.

    Returns:
        True if the API key is 'test_api_key', False otherwise.
    """
    return api_key == 'test_api_key'

# Patch the imported validate_api_key function with our local version
sys.modules['config.api_keys'] = MagicMock()
sys.modules['config.api_keys.validate_api_key'] = validate_api_key

# Test API key path in Auth0JWTBearer.__call__
async def test_auth0_jwt_bearer_with_api_key():
    """Test Auth0JWTBearer middleware with API key."""
    # Create mock request with API key
    mock_request = MagicMock()
    mock_request.headers = {"X-API-Key": "test_api_key"}

    # Patch validate_api_key to return True for our test key
    with patch('apps.api.middleware.auth0.validate_api_key', return_value=True):
        # Create Auth0JWTBearer instance
        auth = Auth0JWTBearer()

        # Call __call__ method
        try:
            result = await auth.__call__(mock_request)
            print("API key authentication successful!")
            print(f"Result: {result}")
            print(f"Request state auth_type: {mock_request.state.auth_type}")
            print(f"Request state user: {mock_request.state.user}")
            return True
        except Exception as e:
            print(f"API key authentication failed: {str(e)}")
            return False

def test_get_user_from_api_key():
    """Test get_user_from_api_key function."""
    user = get_user_from_api_key("test_api_key")
    print(f"User from API key: {user}")
    return user is not None and user.get('id') == 'system'


# Run the tests
if __name__ == '__main__':
    import asyncio

    # Run the async test
    api_key_test_result = asyncio.run(test_auth0_jwt_bearer_with_api_key())
    user_test_result = test_get_user_from_api_key()

    # Print results
    if api_key_test_result and user_test_result:
        print("\nAll tests passed! Auth0JWTBearer middleware supports API keys correctly.")
        sys.exit(0)
    else:
        print("\nTests failed. Auth0JWTBearer middleware needs to be fixed.")
        sys.exit(1)
