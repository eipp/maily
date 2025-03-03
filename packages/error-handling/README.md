# Error Handling Package

This package provides standardized error handling utilities for Maily.

## Features

- **Standardized Error Classes**: A hierarchy of error classes for different error types
- **Error Handlers**: Centralized error handling for different environments and frameworks
- **Error Utilities**: Utilities for error logging, reporting, and formatting
- **Zod Integration**: Built-in support for Zod validation errors

## Installation

```bash
npm install @maily/error-handling
```

## Basic Usage

```typescript
import { ValidationError, ApplicationError } from '@maily/error-handling';

// Create a validation error
const validationError = new ValidationError('Invalid input');
validationError.addError('email', 'Email is required');
validationError.addError('email', 'Email must be valid');

// Check validation errors
if (validationError.hasErrors()) {
  console.log(validationError.getFieldErrors('email'));
}

// Create a custom application error
const customError = new ApplicationError(
  'Something went wrong',
  'CUSTOM_ERROR',
  500,
  { additional: 'details' }
);

// Convert error to JSON for logging
console.log(customError.toJSON());

// Create API response from error
const response = customError.toResponse();
```

## Error Classes

The package provides the following error classes:

- `ApplicationError`: Base error class for all application errors
- `ValidationError`: Error for validation failures
- `AuthenticationError`: Error for authentication failures
- `AuthorizationError`: Error for authorization failures
- `NotFoundError`: Error for resource not found
- `ConflictError`: Error for resource conflicts
- `RateLimitError`: Error for rate limiting
- `ServerError`: Error for server-side issues
- `NetworkError`: Error for network issues
- `TimeoutError`: Error for operation timeouts

## Error Handlers

The package provides error handlers for different environments:

```typescript
import { errorHandler, apiErrorHandler } from '@maily/error-handling';

// Use in Express
app.use(apiErrorHandler());

// Use as a standalone handler
try {
  // Some code that might throw
} catch (error) {
  errorHandler.handle(error);
}
```

## Zod Integration

The package provides integration with Zod for validation:

```typescript
import { z } from 'zod';
import { ValidationError, zodErrorFormatter } from '@maily/error-handling';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

try {
  schema.parse({ email: 'invalid', password: '123' });
} catch (error) {
  // Convert Zod error to ValidationError
  const validationError = ValidationError.fromZodError(error);
  
  // Or format the Zod error
  const formatted = zodErrorFormatter(error);
  console.log(formatted);
}
```