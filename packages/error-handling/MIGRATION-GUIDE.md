# Error Handling Migration Guide

This guide helps you migrate from the legacy error handling to the standardized error handling system.

## Python Migration

### Before:

```python
from errors.exceptions import NotFoundError, DatabaseError, AuthenticationError

def get_resource(resource_id):
    if not resource_exists(resource_id):
        raise NotFoundError(f"Resource {resource_id} not found")
```

### After:

```python
from packages.error_handling.python.error import ResourceNotFoundError, DatabaseError, UnauthorizedError

def get_resource(resource_id):
    if not resource_exists(resource_id):
        raise ResourceNotFoundError(f"Resource {resource_id} not found")
```

### Legacy Error Class Mapping

| Old Error Class | New Error Class |
|----------------|-----------------|
| `NotFoundError` | `ResourceNotFoundError` |
| `AuthenticationError` | `UnauthorizedError` |
| `PermissionDeniedError` | `ForbiddenError` |
| `ValidationError` | `ValidationError` |
| `DatabaseError` | `DatabaseError` |
| `ServiceUnavailableError` | `ServiceUnavailableError` |
| `AIServiceError` | `AIError` |

## FastAPI Middleware Migration

### Before:

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from errors.error_handler import http_exception_handler, validation_exception_handler

app = FastAPI()

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

### After:

```python
from fastapi import FastAPI
from packages.error_handling.python.middleware import setup_error_handling

app = FastAPI()

# Add standardized error handling
setup_error_handling(app)
```

## React ErrorBoundary Migration

### Before:

```tsx
import { ErrorBoundary } from 'apps/web/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundaryWrapper>
      <YourComponent />
    </ErrorBoundaryWrapper>
  );
}
```

### After:

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

## Common Migration Tasks

1. Replace imports from `errors/exceptions.py` with imports from `packages.error_handling.python.error`
2. Replace custom error middleware with `setup_error_handling(app)`
3. Replace imports from `app/web/components/ErrorBoundary` with `packages/error-handling/src/react/ErrorBoundary`
4. Replace API provider-specific error mappings with `map_provider_error` function
5. Use `handle_common_exceptions` decorator for standardized service error handling

## Testing Considerations

- ErrorBoundary tests need to be updated to match the new component structure
- Error middleware tests should verify that status codes and error response format matches expectations
- Error mapping tests should confirm proper conversion between provider errors and standardized errors

## Support

If you need help with the migration, please refer to:

1. `packages/error-handling/README.md` for full documentation
2. Error handling examples in the codebase
3. `ERROR-HANDLING-STANDARDIZATION.md` for a high-level overview