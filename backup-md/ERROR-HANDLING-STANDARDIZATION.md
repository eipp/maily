# Error Handling Standardization

This document outlines the error handling standardization implemented across the Maily application.

## Purpose

The goal of this standardization is to:
1. Establish consistent error handling patterns across all services
2. Improve developer experience with clear error messages
3. Enhance debugging by including trace IDs and timestamps
4. Provide better user experience with appropriate error responses
5. Make error tracking and monitoring more effective

## Components

### Python Error Handling

The standardized error handling for Python services is provided by:

```
packages/error-handling/python/error.py
packages/error-handling/python/middleware.py
```

#### Key Features

- Unified error hierarchy with `MailyError` as the base class
- Standard error codes and HTTP status codes
- Automatic logging with severity-based levels
- Trace IDs for tracking errors across services
- Support for detailed error information
- Provider-specific error mappings (OpenAI, Anthropic, Google)
- Documentation links for each error type

#### Usage Example

```python
from packages.error_handling.python.error import ResourceNotFoundError, DatabaseError

# Raising standardized errors
try:
    result = await fetch_resource(resource_id)
    if not result:
        raise ResourceNotFoundError(f"Resource {resource_id} not found")
except Exception as e:
    raise DatabaseError(f"Database error: {str(e)}")
```

### JavaScript/TypeScript Error Handling

The standardized error handling for JS/TS services is provided by:

```
packages/error-handling/src/errors/ApplicationError.ts
packages/error-handling/src/errors/ErrorTypes.ts
```

#### Key Features

- Type-safe error hierarchy with `ApplicationError` as the base class
- Standardized error types and codes
- Metadata and context support
- Integration with monitoring tools

#### Usage Example

```typescript
import { ApplicationError, ErrorType } from 'packages/error-handling';

try {
  // Some operation that might fail
} catch (error) {
  throw new ApplicationError(
    'Failed to process data', 
    ErrorType.DATA_PROCESSING_ERROR,
    { originalError: error }
  );
}
```

### React Error Handling

For React components, a standardized error boundary is provided:

```
packages/error-handling/src/react/ErrorBoundary.tsx
```

#### Key Features

- Catches and displays errors in React component trees
- Customizable fallback UI
- Error reset functionality
- Integration with analytics/monitoring tools
- TypeScript support

#### Usage Example

```tsx
import { ErrorBoundary } from 'packages/error-handling/src/react/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary 
      fallback={({ error, reset }) => (
        <div>
          <h2>Something went wrong</h2>
          <button onClick={reset}>Try again</button>
        </div>
      )}
    >
      <YourComponent />
    </ErrorBoundary>
  );
}
```

## API Response Format

Standardized error responses follow this format:

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

## Implementation Status

- [x] Core error classes defined
- [x] API middleware integration
- [x] React error boundary component
- [x] Documentation
- [x] Legacy code migration
- [ ] Error documentation pages

## Migration Guide

For detailed migration instructions, please refer to `packages/error-handling/MIGRATION-GUIDE.md`.