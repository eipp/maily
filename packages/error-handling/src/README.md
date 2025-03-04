# Error Handling Standardization

This package provides a standardized approach to error handling across the Maily application.

## Features

- Consistent error class hierarchy
- Standardized error response format
- Integrated logging and monitoring
- Support for both Python and TypeScript
- Error boundary components for React
- Middleware for API error handling

## Usage Guidelines

### Python

```python
from packages.error-handling.python import MailyError, ValidationError, handle_common_exceptions

# Using error classes
try:
    # Some operation
    if not valid:
        raise ValidationError("Invalid input", details={"field": "email"})
except MailyError as e:
    # Handle the error
    response = e.to_response()

# Using decorators
@handle_common_exceptions
async def my_function():
    # This function will have standardized error handling
    pass
```

### TypeScript/JavaScript

```typescript
import { ApplicationError, ValidationError } from 'packages/error-handling';

// Using error classes
try {
    // Some operation
    if (!valid) {
        throw new ValidationError('Invalid input', { field: 'email' });
    }
} catch (error) {
    if (error instanceof ApplicationError) {
        // Handle the error
        const response = error.toResponse();
    }
}
```

### React Components

```jsx
import { ErrorBoundary } from 'packages/error-handling/react';

function MyComponent() {
    return (
        <ErrorBoundary fallback={<ErrorFallback />}>
            {/* Component content */}
        </ErrorBoundary>
    );
}
```

## Error Hierarchy

### Python

- `MailyError` (base class)
  - HTTP Errors
    - `BadRequestError`
    - `UnauthorizedError`
    - `ForbiddenError`
    - `NotFoundError`
    - `ConflictError`
    - `TooManyRequestsError`
    - `ServerError`
  - Domain Errors
    - `AIError`
    - `DatabaseError`
    - `IntegrationError`
    - `BlockchainError`
    - etc.

### TypeScript

- `ApplicationError` (base class)
  - `HttpError`
    - `BadRequestError`
    - `UnauthorizedError`
    - `ForbiddenError`
    - `NotFoundError`
    - `ConflictError`
    - `TooManyRequestsError`
    - `ServerError`
  - Domain Errors
    - `AIError`
    - `DatabaseError`
    - `IntegrationError`
    - `BlockchainError`
    - etc.

## Response Format

All errors serialize to a consistent format:

```json
{
  "error": true,
  "error_code": "validation_error",
  "message": "The request was invalid",
  "status_code": 400,
  "request_id": "req_123456",
  "timestamp": 1598918400,
  "details": [
    {
      "code": "validation.required",
      "message": "This field is required",
      "field": "email"
    }
  ],
  "documentation_url": "https://docs.maily.com/errors/validation_error"
}
```

## Migration Guide

1. Replace imports from legacy files with imports from this package
2. Update error handling to use the new standardized classes
3. Implement the error middleware in FastAPI applications
4. Use the ErrorBoundary component in React applications