# Maily API Fixed Tests

This directory contains fixed tests for the Maily API. The original test suite had several issues that prevented it from running successfully:

## Issues Fixed

1. **Dependency Conflicts**:
   - Fixed by creating a `requirements-lock.txt` file with compatible package versions
   - Resolved conflicts between FastAPI 0.95.1 and prometheus-fastapi-instrumentator 7.0.0

2. **Pytest Configuration**:
   - Fixed duplicate `addopts` settings in pytest.ini that prevented tests from running

3. **Code Structure Mismatch**:
   - The original test suite references a module structure that doesn't match the current project organization
   - Original tests use imports from `backend.ai`, but the project has been refactored to use a different structure

4. **Import Problems**:
   - Fixed relative imports in the main application by creating a standalone version that doesn't rely on relative imports
   - Created a fixed `main_fixed.py` file that can be used for testing without import issues

## Running the Tests

You can run the fixed tests using the following commands:

```bash
# Install required dependencies
pip install -r requirements-lock.txt

# Run all fixed tests
python -m pytest fixed_tests/ -v

# Run specific test file
python -m pytest fixed_tests/test_health.py -v

# Run specific test
python -m pytest fixed_tests/test_health.py::test_health_check -v
```

## Test Structure

- `conftest.py`: Contains pytest fixtures for testing
- `test_health.py`: Tests the health check endpoints
- `test_campaigns.py`: Tests the campaign and model configuration endpoints

## Moving Forward

To fully integrate these fixes into the main codebase, you should:

1. Update the `main.py` file to use absolute imports instead of relative imports
2. Update the original test suite to match the current project structure
3. Create proper mocks for AI components in the test suite
4. Run tests before each deployment to ensure API stability

## Debugging

If you encounter issues when running the tests:

1. Check that you have installed all required dependencies
2. Ensure that the import paths in the test files match your project structure
3. Look for error messages about missing modules or import errors
4. Use the `simple_test.py` script to verify basic functionality

For more thorough testing, you might want to set up a CI/CD pipeline that includes:

- Running these tests automatically on each commit
- Linting the codebase to catch potential issues
- Integration tests with a real database (potentially using Docker)
