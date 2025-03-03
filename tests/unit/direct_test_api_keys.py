"""Direct test for API key functionality without pytest dependencies."""
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Try importing the API key modules
try:
    from apps.api.config.api_keys import validate_api_key, API_KEYS
    from apps.api.middleware.auth0 import get_user_from_api_key
    print("Successfully imported API key modules")
except Exception as e:
    print(f"Error importing modules: {str(e)}")
    sys.exit(1)

# Test API key validation
def test_api_key_validation():
    """Test the API key validation function."""
    # The test_api_key is defined in our configuration
    assert "test_api_key" in API_KEYS, "test_api_key should be in API_KEYS"
    assert validate_api_key("test_api_key") is True, "validate_api_key should return True for valid key"
    assert validate_api_key("invalid_key") is False, "validate_api_key should return False for invalid key"
    print("API key validation test passed")

# Test get_user_from_api_key
def test_get_user_from_api_key():
    """Test the get_user_from_api_key function."""
    user = get_user_from_api_key("test_api_key")
    assert user is not None, "get_user_from_api_key should return a user"
    assert user.get("id") == "system", "User ID should be 'system'"
    assert "roles" in user, "User should have roles"
    assert "system" in user.get("roles"), "User should have 'system' role"
    print("get_user_from_api_key test passed")

if __name__ == "__main__":
    # Run the tests
    try:
        test_api_key_validation()
        test_get_user_from_api_key()
        print("\nAll tests passed! API key functionality is working correctly.")
    except AssertionError as e:
        print(f"\nTest failed: {str(e)}")
        sys.exit(1)
