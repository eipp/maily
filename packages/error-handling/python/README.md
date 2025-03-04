# Maily Error Handling for Python

This package provides standardized error handling for Python services in the Maily platform.

## Features

- Standardized error classes with consistent properties
- FastAPI middleware for automatic error handling
- Integration with logging and monitoring
- Error serialization for consistent API responses

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Error Handling

```python
from packages.error_handling.python.errors import ApplicationError, ValidationError, NotFoundError

# Create and raise an error
try:
    # Some operation that might fail
    if not valid_input:
        raise ValidationError(
            message="Invalid input",
            details={"field": "email", "error": "Invalid email format"},
            request_id="req_12345"
        )
except ApplicationError as e:
    # All errors have standard properties
    print(e.message)  # Error message
    print(e.error_code)  # Error code
    print(e.status_code)  # HTTP status code
    print(e.to_dict())  # Convert to dictionary
    print(e.to_response())  # Create API response
```

### FastAPI Integration

```python
from fastapi import FastAPI
from packages.error_handling.python.middleware import add_error_handling

app = FastAPI()

# Add error handling middleware
add_error_handling(app)

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    # Errors raised here will be automatically handled
    if item_id <= 0:
        raise ValidationError("Item ID must be positive")
    
    item = database.get_item(item_id)
    if not item:
        raise NotFoundError(f"Item with ID {item_id} not found")
    
    return item
```

## Error Classes

### Base Errors

- `ApplicationError` - Base error class
- `HttpError` - Base for HTTP errors

### HTTP Errors

- `BadRequestError` - 400 Bad Request
- `UnauthorizedError` - 401 Unauthorized
- `ForbiddenError` - 403 Forbidden
- `NotFoundError` - 404 Not Found
- `ConflictError` - 409 Conflict
- `ValidationError` - 422 Unprocessable Entity
- `TooManyRequestsError` - 429 Too Many Requests
- `ServerError` - 500 Internal Server Error
- `ServiceUnavailableError` - 503 Service Unavailable

### Domain Errors

- `AIError` - AI service errors
- `ModelError` - AI model errors
- `BlockchainError` - Blockchain errors
- `IntegrationError` - External integration errors
- `DatabaseError` - Database errors
- `ConfigurationError` - Configuration errors
- `QuotaExceededError` - Quota exceeded errors
- `NetworkError` - Network errors
- `TimeoutError` - Timeout errors
- `ContentFilterError` - Content moderation errors