/**
 * Base class for all application errors
 * 
 * This provides a standardized way to create and handle errors throughout
 * the application with consistent properties and serialization.
 */
export class ApplicationError extends Error {
  /**
   * The unique error code (e.g., 'RESOURCE_NOT_FOUND', 'VALIDATION_ERROR')
   */
  public readonly code: string;

  /**
   * HTTP status code associated with this error
   */
  public readonly statusCode: number;

  /**
   * Additional details about the error (e.g., validation issues, field-specific errors)
   */
  public readonly details?: Record<string, any>;

  /**
   * A trace ID to correlate logs with error responses
   */
  public readonly traceId?: string;

  /**
   * Create a new application error
   * 
   * @param message Human-readable error message
   * @param code Unique error code for programmatic handling
   * @param statusCode HTTP status code
   * @param details Additional error details
   */
  constructor(
    message: string,
    code: string,
    statusCode: number = 500,
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message);

    // Maintain proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, ApplicationError.prototype);
    
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.traceId = traceId;

    // Capture stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert the error to a plain object for serialization
   */
  public toJSON(): Record<string, any> {
    const errorResponse: Record<string, any> = {
      error: {
        code: this.code,
        message: this.message,
        statusCode: this.statusCode,
      }
    };

    if (this.details) {
      errorResponse.error.details = this.details;
    }

    if (this.traceId) {
      errorResponse.error.traceId = this.traceId;
    }

    return errorResponse;
  }

  /**
   * Convert the error to a response format suitable for API responses
   */
  public toResponse(): {
    statusCode: number;
    body: Record<string, any>;
  } {
    return {
      statusCode: this.statusCode,
      body: this.toJSON(),
    };
  }
}