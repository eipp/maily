# Maily Error Handling Package

A standardized error handling package for the Maily platform.

## Installation

```bash
npm install @maily/error-handling
```

## Usage

### Basic Usage

```typescript
import { ApplicationError, NotFoundError } from '@maily/error-handling';

// Create a custom error
throw new ApplicationError('Something went wrong', 'CUSTOM_ERROR', 500);

// Use pre-defined errors
throw new NotFoundError('User not found', { userId: '123' });
```

### Domain-Specific Errors

```typescript
import { 
  CampaignNotFoundError, 
  TemplateRenderingError 
} from '@maily/error-handling';

// Campaign errors
throw new CampaignNotFoundError('campaign-123');

// Template errors
throw new TemplateRenderingError('template-456', { 
  missingVariables: ['name', 'email'] 
});
```

### Error Handling in Express

```typescript
import { errorHandler } from '@maily/error-handling/handlers';

// Add middleware
app.use(errorHandler());

// In your route handlers
app.get('/users/:id', async (req, res, next) => {
  try {
    const user = await userService.findById(req.params.id);
    if (!user) {
      throw new NotFoundError(`User with ID ${req.params.id} not found`);
    }
    res.json(user);
  } catch (error) {
    next(error);
  }
});
```

### Error Handling in FastAPI

```python
from packages.error_handling.middleware import error_handler
from packages.error_handling.errors import NotFoundError

app.add_middleware(error_handler)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await user_service.find_by_id(user_id)
    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")
    return user
```

### React Error Boundary

```tsx
import { ErrorBoundary } from '@maily/error-handling/react';

function App() {
  return (
    <ErrorBoundary fallback={<ErrorPage />}>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### Using Error Hooks

```tsx
import { useErrorHandler } from '@maily/error-handling/react';

function UserProfile({ userId }) {
  const handleError = useErrorHandler();
  
  useEffect(() => {
    async function fetchUser() {
      try {
        const user = await api.getUser(userId);
        setUser(user);
      } catch (error) {
        handleError(error);
      }
    }
    
    fetchUser();
  }, [userId, handleError]);
  
  // ...
}
```

## Available Error Classes

### Base Errors

- `ApplicationError`: Base error class
- `ValidationError`: For validation errors

### HTTP Errors

- `BadRequestError`: 400 Bad Request
- `UnauthorizedError`: 401 Unauthorized
- `ForbiddenError`: 403 Forbidden
- `NotFoundError`: 404 Not Found
- `ConflictError`: 409 Conflict
- `UnprocessableEntityError`: 422 Unprocessable Entity
- `TooManyRequestsError`: 429 Too Many Requests
- `InternalServerError`: 500 Internal Server Error
- `BadGatewayError`: 502 Bad Gateway
- `ServiceUnavailableError`: 503 Service Unavailable
- `GatewayTimeoutError`: 504 Gateway Timeout

### Domain Errors

- User Errors: `UserError`, `UserNotFoundError`
- Auth Errors: `AuthenticationError`, `InvalidCredentialsError`, `TokenExpiredError`
- Campaign Errors: `CampaignError`, `CampaignNotFoundError`, `CampaignAlreadyExistsError`
- Template Errors: `TemplateError`, `TemplateNotFoundError`, `TemplateRenderingError`
- AI Errors: `AIError`, `ModelNotAvailableError`, `ContentModerationError`

## Best Practices

1. **Use Specific Error Types**: Use the most specific error type that matches your error condition.

2. **Include Useful Details**: Add relevant details to help with debugging.

3. **Use Consistent Status Codes**: Follow HTTP standards for status codes.

4. **Use Error Boundaries in React**: Wrap components in ErrorBoundary to gracefully handle errors.

5. **Handle Errors at the Right Level**: Handle errors at the appropriate abstraction level.

6. **Log Errors**: Log errors for monitoring and debugging.

7. **Provide User-Friendly Messages**: Ensure error messages are helpful to end-users.

## Error Response Format

All errors are transformed into a consistent response format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 123 not found",
    "statusCode": 404,
    "details": {
      "userId": "123"
    },
    "traceId": "4f90a2f8-9b6d-4098-8a80-35e7c0f5317d",
    "severity": "medium",
    "category": "not_found"
  }
}
```