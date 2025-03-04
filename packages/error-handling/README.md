# Maily Error Handling

A standardized error handling system for the Maily application.

## Overview

This package provides a unified approach to error handling across all Maily services, with components for:

- Python backends (FastAPI)
- JavaScript/TypeScript frontends
- React components

## Installation

The package is pre-installed as part of the Maily monorepo.

## Python Usage

### Basic Error Classes

```python
from packages.error_handling.python.error import MailyError, ResourceNotFoundError, ValidationError

# Raising a basic error
raise MailyError("Something went wrong")

# Raising a more specific error
raise ResourceNotFoundError("User not found", 
                           details={"user_id": "123"})

# With trace ID and provider info
raise ValidationError("Invalid parameters",
                     trace_id="abcd-1234",
                     provider="openai",
                     request_id="req_123")
```

### Error Middleware for FastAPI

```python
from fastapi import FastAPI
from packages.error_handling.python.middleware import setup_error_handling

app = FastAPI()

# Add standardized error handling
setup_error_handling(app)
```

### Provider Error Mapping

```python
from packages.error_handling.python.error import map_provider_error

try:
    # OpenAI API call
    response = await openai.Completion.create(...)
except Exception as e:
    # Map to standardized error
    error = map_provider_error(
        provider="openai",
        error_type=e.type,
        message=str(e),
        request_id=e.request_id
    )
    raise error
```

## TypeScript Usage

### Basic Error Classes

```typescript
import { ApplicationError, ErrorType } from 'packages/error-handling';

// Basic error
throw new ApplicationError('Something went wrong');

// With error type and status
throw new ApplicationError(
  'Resource not found', 
  ErrorType.NOT_FOUND,
  404
);

// With metadata
throw new ApplicationError(
  'Invalid parameters',
  ErrorType.VALIDATION_ERROR,
  400,
  { fields: ['email', 'password'] }
);
```

## React Usage

### Basic ErrorBoundary

```tsx
import { ErrorBoundary } from 'packages/error-handling/src/react/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### Custom Fallback UI

```tsx
import { ErrorBoundary } from 'packages/error-handling/src/react/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary
      fallback={({ error, reset }) => (
        <div>
          <h2>Oh no! Something went wrong</h2>
          <p>{error.message}</p>
          <button onClick={reset}>Try Again</button>
        </div>
      )}
      onError={(error) => {
        // Log to monitoring service
        console.error('Component error:', error);
      }}
    >
      <YourComponent />
    </ErrorBoundary>
  );
}
```

## Error Response Format

All API errors are returned in this standardized format:

```json
{
  "error": true,
  "error_code": "not_found",
  "message": "Resource not found",
  "status_code": 404,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1717574880.123,
  "details": [
    {
      "code": "not_found.details",
      "message": "Error details",
      "field": "resource_id"
    }
  ],
  "documentation_url": "https://docs.maily.com/errors/not_found"
}
```

## Documentation

- See `MIGRATION-GUIDE.md` for instructions on migrating from legacy error handling.
- See `ERROR-HANDLING-STANDARDIZATION.md` in the root directory for a high-level overview of the standardization effort.