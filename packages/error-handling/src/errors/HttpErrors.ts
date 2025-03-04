import { ApplicationError } from './ApplicationError';
import { ErrorCode, ErrorDetail } from './ErrorTypes';

/**
 * Base class for HTTP 400 Bad Request errors
 */
export class BadRequestError extends ApplicationError {
  constructor(
    message: string = 'The request was invalid',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.BAD_REQUEST,
      400,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for validation failures
 */
export class ValidationError extends BadRequestError {
  constructor(
    message: string = 'Validation error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.VALIDATION_ERROR;
  }
}

/**
 * Error for duplicate resources
 */
export class DuplicateResourceError extends BadRequestError {
  constructor(
    message: string = 'Resource already exists',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.ALREADY_EXISTS;
    this.statusCode = 409;
  }
}

/**
 * Error for conflicting resources
 */
export class ConflictError extends BadRequestError {
  constructor(
    message: string = 'The request conflicts with the current state',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.CONFLICT;
    this.statusCode = 409;
  }
}

/**
 * Error for rate limit exceeded
 */
export class RateLimitExceededError extends BadRequestError {
  constructor(
    message: string = 'Rate limit exceeded',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.RATE_LIMIT_EXCEEDED;
    this.statusCode = 429;
  }
}

/**
 * Error for too many requests
 */
export class TooManyRequestsError extends BadRequestError {
  constructor(
    message: string = 'Too many requests, please try again later',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.TOO_MANY_REQUESTS;
    this.statusCode = 429;
  }
}

/**
 * Error for unauthorized access (not authenticated)
 */
export class UnauthorizedError extends ApplicationError {
  constructor(
    message: string = 'Authentication is required',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.UNAUTHORIZED,
      401,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for forbidden access (authenticated but not authorized)
 */
export class ForbiddenError extends ApplicationError {
  constructor(
    message: string = 'You do not have permission to perform this action',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.FORBIDDEN,
      403,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for disabled features
 */
export class FeatureDisabledError extends ForbiddenError {
  constructor(
    message: string = 'This feature is currently disabled',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.FEATURE_DISABLED;
  }
}

/**
 * Error for resources that don't exist
 */
export class NotFoundError extends ApplicationError {
  constructor(
    message: string = 'The requested resource was not found',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.NOT_FOUND,
      404,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for server errors
 */
export class ServerError extends ApplicationError {
  constructor(
    message: string = 'An unexpected error occurred',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.INTERNAL_ERROR,
      500,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for unavailable services
 */
export class ServiceUnavailableError extends ServerError {
  constructor(
    message: string = 'The service is currently unavailable',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.SERVICE_UNAVAILABLE;
    this.statusCode = 503;
  }
}

/**
 * Legacy compatibility class
 */
export class AuthenticationError extends UnauthorizedError {
  constructor(
    message: string = 'Authentication failed',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(message, details, traceId, requestId, provider);
  }
}

/**
 * Legacy compatibility class
 */
export class AuthorizationError extends ForbiddenError {
  constructor(
    message: string = 'Not authorized to perform this action',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(message, details, traceId, requestId, provider);
  }
}