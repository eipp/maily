/**
 * HTTP-specific error classes
 * 
 * These classes represent common HTTP errors with appropriate status codes
 * and standardized error messages. They should be used when returning HTTP
 * responses to clients.
 */

import { ApplicationError } from './ApplicationError';

/**
 * 400 Bad Request
 * Used when the client sends a request with invalid data
 */
export class BadRequestError extends ApplicationError {
  constructor(
    message: string = 'Bad request',
    code: string = 'BAD_REQUEST',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 400, details, traceId);
  }
}

/**
 * 401 Unauthorized
 * Used when authentication is required but not provided or invalid
 */
export class UnauthorizedError extends ApplicationError {
  constructor(
    message: string = 'Authentication required',
    code: string = 'UNAUTHORIZED',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 401, details, traceId);
  }
}

/**
 * 403 Forbidden
 * Used when the authenticated user doesn't have permission to access a resource
 */
export class ForbiddenError extends ApplicationError {
  constructor(
    message: string = 'Access denied',
    code: string = 'FORBIDDEN',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 403, details, traceId);
  }
}

/**
 * 404 Not Found
 * Used when a requested resource doesn't exist
 */
export class NotFoundError extends ApplicationError {
  constructor(
    message: string = 'Resource not found',
    code: string = 'NOT_FOUND',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 404, details, traceId);
  }
}

/**
 * 409 Conflict
 * Used when a request conflicts with the current state of the resource
 */
export class ConflictError extends ApplicationError {
  constructor(
    message: string = 'Resource conflict',
    code: string = 'CONFLICT',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 409, details, traceId);
  }
}

/**
 * 422 Unprocessable Entity
 * Used when validation fails for the provided data
 */
export class ValidationError extends ApplicationError {
  constructor(
    message: string = 'Validation failed',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, 'VALIDATION_ERROR', 422, details, traceId);
  }
}

/**
 * 429 Too Many Requests
 * Used when a client exceeds rate limits
 */
export class TooManyRequestsError extends ApplicationError {
  constructor(
    message: string = 'Rate limit exceeded',
    retryAfter?: number,
    traceId?: string
  ) {
    const details = retryAfter ? { retryAfter } : undefined;
    super(message, 'RATE_LIMIT_EXCEEDED', 429, details, traceId);
  }
}

/**
 * 500 Internal Server Error
 * Used for unexpected server errors
 */
export class InternalServerError extends ApplicationError {
  constructor(
    message: string = 'Internal server error',
    code: string = 'INTERNAL_SERVER_ERROR',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 500, details, traceId);
  }
}

/**
 * 502 Bad Gateway
 * Used when an upstream service returns an invalid response
 */
export class BadGatewayError extends ApplicationError {
  constructor(
    message: string = 'Bad gateway',
    code: string = 'BAD_GATEWAY',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 502, details, traceId);
  }
}

/**
 * 503 Service Unavailable
 * Used when a service is temporarily unavailable
 */
export class ServiceUnavailableError extends ApplicationError {
  constructor(
    message: string = 'Service unavailable',
    code: string = 'SERVICE_UNAVAILABLE',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 503, details, traceId);
  }
}

/**
 * 504 Gateway Timeout
 * Used when an upstream service times out
 */
export class GatewayTimeoutError extends ApplicationError {
  constructor(
    message: string = 'Gateway timeout',
    code: string = 'GATEWAY_TIMEOUT',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 504, details, traceId);
  }
}