/**
 * Standardized Error Handling Framework
 *
 * This module provides a consistent approach to error handling
 * across all services in the Maily platform.
 */

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  /**
   * Critical errors that require immediate attention
   */
  CRITICAL = 'critical',

  /**
   * High severity errors that impact service functionality
   */
  HIGH = 'high',

  /**
   * Medium severity errors that degrade service quality
   */
  MEDIUM = 'medium',

  /**
   * Low severity errors that have minimal impact
   */
  LOW = 'low',

  /**
   * Informational errors for debugging purposes
   */
  INFO = 'info',
}

/**
 * Error categories for classification
 */
export enum ErrorCategory {
  /**
   * Authentication or authorization errors
   */
  AUTHENTICATION = 'authentication',

  /**
   * Input validation errors
   */
  VALIDATION = 'validation',

  /**
   * Business logic errors
   */
  BUSINESS_LOGIC = 'business_logic',

  /**
   * Database operation errors
   */
  DATABASE = 'database',

  /**
   * External service errors
   */
  EXTERNAL_SERVICE = 'external_service',

  /**
   * Network or infrastructure errors
   */
  INFRASTRUCTURE = 'infrastructure',

  /**
   * Internal server errors
   */
  SERVER = 'server',

  /**
   * Unknown or unclassified errors
   */
  UNKNOWN = 'unknown',
}

/**
 * Error context with additional information
 */
export interface ErrorContext {
  /**
   * Source service or component
   */
  source?: string;

  /**
   * Operation being performed
   */
  operation?: string;

  /**
   * Request ID for tracing
   */
  requestId?: string;

  /**
   * User ID (if authenticated)
   */
  userId?: string;

  /**
   * Resource being accessed
   */
  resource?: string;

  /**
   * Additional key-value pairs
   */
  [key: string]: any;
}

/**
 * Error details with structured information
 */
export interface ErrorDetails {
  /**
   * Error code (machine-readable)
   */
  code: string;

  /**
   * Error message (human-readable)
   */
  message: string;

  /**
   * Error category
   */
  category: ErrorCategory;

  /**
   * Error severity
   */
  severity: ErrorSeverity;

  /**
   * Error context
   */
  context?: ErrorContext;

  /**
   * Original error
   */
  originalError?: Error;

  /**
   * Timestamp when the error occurred
   */
  timestamp: Date;

  /**
   * Suggested resolution steps
   */
  resolution?: string;

  /**
   * Stack trace (if available)
   */
  stack?: string;

  /**
   * HTTP status code (if applicable)
   */
  httpStatusCode?: number;
}

/**
 * Base application error class
 */
export class AppError extends Error {
  /**
   * Error code (machine-readable)
   */
  public readonly code: string;

  /**
   * Error category
   */
  public readonly category: ErrorCategory;

  /**
   * Error severity
   */
  public readonly severity: ErrorSeverity;

  /**
   * Error context
   */
  public readonly context: ErrorContext;

  /**
   * Original error
   */
  public readonly originalError?: Error;

  /**
   * Timestamp when the error occurred
   */
  public readonly timestamp: Date;

  /**
   * Suggested resolution steps
   */
  public readonly resolution?: string;

  /**
   * HTTP status code (if applicable)
   */
  public readonly httpStatusCode?: number;

  /**
   * Create a new application error
   * @param details Error details
   */
  constructor(details: Omit<ErrorDetails, 'timestamp' | 'stack'>) {
    super(details.message);

    this.code = details.code;
    this.category = details.category;
    this.severity = details.severity;
    this.context = details.context || {};
    this.originalError = details.originalError;
    this.timestamp = new Date();
    this.resolution = details.resolution;
    this.httpStatusCode = details.httpStatusCode;

    // Capture stack trace
    Error.captureStackTrace(this, this.constructor);

    // Override name property
    this.name = this.constructor.name;
  }

  /**
   * Convert error to plain object for serialization
   * @returns Serializable error object
   */
  public toJSON(): ErrorDetails {
    return {
      code: this.code,
      message: this.message,
      category: this.category,
      severity: this.severity,
      context: this.context,
      timestamp: this.timestamp,
      resolution: this.resolution,
      stack: this.stack,
      httpStatusCode: this.httpStatusCode,
      // Don't include originalError to avoid circular references
    };
  }

  /**
   * Create error response for API
   * @param includeStack Whether to include stack trace
   * @returns API error response
   */
  public toApiResponse(includeStack: boolean = false): any {
    const response: any = {
      error: {
        code: this.code,
        message: this.message,
        category: this.category,
      },
    };

    if (includeStack && this.stack) {
      response.error.stack = this.stack;
    }

    return response;
  }

  /**
   * Get HTTP status code for this error
   * @returns HTTP status code
   */
  public getHttpStatusCode(): number {
    // Return explicit status code if set
    if (this.httpStatusCode) {
      return this.httpStatusCode;
    }

    // Derive status code from category
    switch (this.category) {
      case ErrorCategory.AUTHENTICATION:
        return 401;
      case ErrorCategory.VALIDATION:
        return 400;
      case ErrorCategory.BUSINESS_LOGIC:
        return 422;
      case ErrorCategory.DATABASE:
        return 500;
      case ErrorCategory.EXTERNAL_SERVICE:
        return 502;
      case ErrorCategory.INFRASTRUCTURE:
        return 503;
      case ErrorCategory.SERVER:
        return 500;
      default:
        return 500;
    }
  }
}

/**
 * Validation error class
 */
export class ValidationError extends AppError {
  /**
   * Field validation errors
   */
  public readonly validationErrors: Record<string, string>;

  /**
   * Create a new validation error
   * @param message Error message
   * @param validationErrors Field validation errors
   * @param context Error context
   */
  constructor(
    message: string = 'Validation failed',
    validationErrors: Record<string, string> = {},
    context: ErrorContext = {}
  ) {
    super({
      code: 'VALIDATION_ERROR',
      message,
      category: ErrorCategory.VALIDATION,
      severity: ErrorSeverity.MEDIUM,
      context,
      httpStatusCode: 400,
    });

    this.validationErrors = validationErrors;
  }

  /**
   * Convert error to API response
   * @param includeStack Whether to include stack trace
   * @returns API error response
   */
  public override toApiResponse(includeStack: boolean = false): any {
    const response = super.toApiResponse(includeStack);
    response.error.validationErrors = this.validationErrors;
    return response;
  }
}

/**
 * Authentication error class
 */
export class AuthenticationError extends AppError {
  /**
   * Create a new authentication error
   * @param message Error message
   * @param code Error code
   * @param context Error context
   */
  constructor(
    message: string = 'Authentication failed',
    code: string = 'AUTHENTICATION_ERROR',
    context: ErrorContext = {}
  ) {
    super({
      code,
      message,
      category: ErrorCategory.AUTHENTICATION,
      severity: ErrorSeverity.HIGH,
      context,
      httpStatusCode: 401,
    });
  }
}

/**
 * Not found error class
 */
export class NotFoundError extends AppError {
  /**
   * Create a new not found error
   * @param resource Resource type
   * @param id Resource ID
   * @param context Error context
   */
  constructor(
    resource: string,
    id?: string,
    context: ErrorContext = {}
  ) {
    const message = id
      ? `${resource} with ID ${id} not found`
      : `${resource} not found`;

    super({
      code: 'RESOURCE_NOT_FOUND',
      message,
      category: ErrorCategory.BUSINESS_LOGIC,
      severity: ErrorSeverity.LOW,
      context: {
        ...context,
        resource,
        resourceId: id,
      },
      httpStatusCode: 404,
    });
  }
}

/**
 * External service error class
 */
export class ExternalServiceError extends AppError {
  /**
   * Create a new external service error
   * @param serviceName External service name
   * @param message Error message
   * @param originalError Original error
   * @param context Error context
   */
  constructor(
    serviceName: string,
    message: string = 'External service error',
    originalError?: Error,
    context: ErrorContext = {}
  ) {
    super({
      code: 'EXTERNAL_SERVICE_ERROR',
      message: `${serviceName}: ${message}`,
      category: ErrorCategory.EXTERNAL_SERVICE,
      severity: ErrorSeverity.HIGH,
      context: {
        ...context,
        serviceName,
      },
      originalError,
      httpStatusCode: 502,
    });
  }
}

/**
 * Database error class
 */
export class DatabaseError extends AppError {
  /**
   * Create a new database error
   * @param operation Database operation
   * @param message Error message
   * @param originalError Original error
   * @param context Error context
   */
  constructor(
    operation: string,
    message: string = 'Database operation failed',
    originalError?: Error,
    context: ErrorContext = {}
  ) {
    super({
      code: 'DATABASE_ERROR',
      message: `${operation}: ${message}`,
      category: ErrorCategory.DATABASE,
      severity: ErrorSeverity.HIGH,
      context: {
        ...context,
        operation,
      },
      originalError,
      httpStatusCode: 500,
    });
  }
}

/**
 * Rate limit error class
 */
export class RateLimitError extends AppError {
  /**
   * Create a new rate limit error
   * @param resource Resource being rate limited
   * @param limit Rate limit
   * @param reset When rate limit resets
   * @param context Error context
   */
  constructor(
    resource: string,
    limit: number,
    reset: Date,
    context: ErrorContext = {}
  ) {
    super({
      code: 'RATE_LIMIT_EXCEEDED',
      message: `Rate limit exceeded for ${resource}`,
      category: ErrorCategory.BUSINESS_LOGIC,
      severity: ErrorSeverity.MEDIUM,
      context: {
        ...context,
        resource,
        limit,
        reset: reset.toISOString(),
      },
      httpStatusCode: 429,
      resolution: `Try again after ${reset.toISOString()}`,
    });
  }

  /**
   * Convert error to API response
   * @param includeStack Whether to include stack trace
   * @returns API error response
   */
  public override toApiResponse(includeStack: boolean = false): any {
    const response = super.toApiResponse(includeStack);
    response.error.retryAfter = this.context.reset;
    return response;
  }
}

/**
 * Internal server error class
 */
export class InternalServerError extends AppError {
  /**
   * Create a new internal server error
   * @param message Error message
   * @param originalError Original error
   * @param context Error context
   */
  constructor(
    message: string = 'Internal server error',
    originalError?: Error,
    context: ErrorContext = {}
  ) {
    super({
      code: 'INTERNAL_SERVER_ERROR',
      message,
      category: ErrorCategory.SERVER,
      severity: ErrorSeverity.HIGH,
      context,
      originalError,
      httpStatusCode: 500,
    });
  }
}

/**
 * Access denied error class
 */
export class AccessDeniedError extends AppError {
  /**
   * Create a new access denied error
   * @param resource Resource being accessed
   * @param permission Required permission
   * @param context Error context
   */
  constructor(
    resource: string,
    permission?: string,
    context: ErrorContext = {}
  ) {
    let message = `Access denied to ${resource}`;
    if (permission) {
      message += ` (missing permission: ${permission})`;
    }

    super({
      code: 'ACCESS_DENIED',
      message,
      category: ErrorCategory.AUTHENTICATION,
      severity: ErrorSeverity.MEDIUM,
      context: {
        ...context,
        resource,
        requiredPermission: permission,
      },
      httpStatusCode: 403,
    });
  }
}

/**
 * Convert an unknown error to an AppError
 * @param error Unknown error
 * @param context Error context
 * @returns Application error
 */
export function normalizeError(error: unknown, context: ErrorContext = {}): AppError {
  // If already an AppError, create a new instance with merged context
  if (error instanceof AppError) {
    return new AppError({
      code: error.code,
      message: error.message,
      category: error.category,
      severity: error.severity,
      context: { ...error.context, ...context },
      originalError: error.originalError,
      resolution: error.resolution,
      httpStatusCode: error.httpStatusCode
    });
  }

  // Handle plain Error objects
  if (error instanceof Error) {
    return new InternalServerError(
      error.message,
      error,
      context
    );
  }

  // Handle string errors
  if (typeof error === 'string') {
    return new InternalServerError(
      error,
      undefined,
      context
    );
  }

  // Handle other types
  return new InternalServerError(
    'An unknown error occurred',
    undefined,
    {
      ...context,
      originalValue: error,
    }
  );
}

/**
 * Error handler middleware for Express
 * @param err Error object
 * @param req Request object
 * @param res Response object
 * @param next Next function
 */
export function errorHandlerMiddleware(err: any, req: any, res: any, next: any): void {
  // Skip if headers already sent
  if (res.headersSent) {
    return next(err);
  }

  // Create error context from request
  const context: ErrorContext = {
    requestId: req.id || req.headers['x-request-id'],
    userId: req.user?.id,
    path: req.path,
    method: req.method,
    ip: req.ip,
  };

  // Normalize the error
  const appError = normalizeError(err, context);

  // Determine status code
  const statusCode = appError.getHttpStatusCode();

  // Log error
  const logger = req.logger || console;
  if (statusCode >= 500) {
    logger.error('Server error', appError.toJSON());
  } else {
    logger.warn('Client error', appError.toJSON());
  }

  // Send response
  res.status(statusCode).json(
    appError.toApiResponse(process.env.NODE_ENV === 'development')
  );
}

/**
 * Async error handler for Express route handlers
 * @param fn Async route handler
 * @returns Route handler with error handling
 */
export function asyncHandler(fn: Function): Function {
  return function(req: any, res: any, next: any): Promise<any> {
    return Promise.resolve(fn(req, res, next)).catch(next);
  };
}

export default {
  AppError,
  ValidationError,
  AuthenticationError,
  NotFoundError,
  ExternalServiceError,
  DatabaseError,
  RateLimitError,
  InternalServerError,
  AccessDeniedError,
  ErrorCategory,
  ErrorSeverity,
  normalizeError,
  errorHandlerMiddleware,
  asyncHandler,
};
