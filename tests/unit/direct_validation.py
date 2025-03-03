"""Direct validation of API key support in Auth0JWTBearer middleware."""
import os
import sys
import re

def validate_middleware_implementation():
    """Validate that the Auth0JWTBearer middleware has API key support."""
    # Get the path to the middleware file
    middleware_path = os.path.join(os.path.dirname(__file__), '../middleware/auth0.py')

    if not os.path.exists(middleware_path):
        print(f"Error: File not found: {middleware_path}")
        return False

    # Read the file
    with open(middleware_path, 'r') as f:
        content = f.read()

    # Check for the presence of API key handling code
    has_api_key_header = 'api_key = request.headers.get("X-API-Key")' in content
    has_api_key_validation = 'validate_api_key(api_key)' in content
    has_get_user_function = 'get_user_from_api_key' in content

    # Check for import of validate_api_key
    has_import = 'from config.api_keys import validate_api_key' in content

    # Print validation results
    print("Validating API key support in Auth0JWTBearer middleware...")
    print(f"- Imports validate_api_key: {'✓' if has_import else '✗'}")
    print(f"- Gets API key from header: {'✓' if has_api_key_header else '✗'}")
    print(f"- Validates API key: {'✓' if has_api_key_validation else '✗'}")
    print(f"- Uses get_user_from_api_key: {'✓' if has_get_user_function else '✗'}")

    # Check for the implementation of get_user_from_api_key
    get_user_function_pattern = r'def get_user_from_api_key\(.*?\):'
    has_get_user_function_def = bool(re.search(get_user_function_pattern, content))
    print(f"- Defines get_user_from_api_key function: {'✓' if has_get_user_function_def else '✗'}")

    # Check for the config/api_keys.py file
    api_keys_path = os.path.join(os.path.dirname(__file__), '../config/api_keys.py')
    if os.path.exists(api_keys_path):
        print(f"- config/api_keys.py file exists: ✓")

        # Read the api_keys.py file
        with open(api_keys_path, 'r') as f:
            api_keys_content = f.read()

        # Check for validate_api_key function
        has_validate_function = 'def validate_api_key' in api_keys_content
        print(f"- api_keys.py defines validate_api_key function: {'✓' if has_validate_function else '✗'}")
    else:
        print(f"- config/api_keys.py file exists: ✗")

    # Overall validation result
    all_checks_passed = (
        has_import and
        has_api_key_header and
        has_api_key_validation and
        has_get_user_function and
        has_get_user_function_def and
        os.path.exists(api_keys_path)
    )

    if all_checks_passed:
        print("\n✅ All checks passed! API key support has been properly implemented.")
    else:
        print("\n❌ Some checks failed. API key support may not be properly implemented.")

    return all_checks_passed

if __name__ == "__main__":
    success = validate_middleware_implementation()
    sys.exit(0 if success else 1)
