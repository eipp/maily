/**
 * Base error class for all application errors
 */
export class ApplicationError extends Error {
  /**
   * Error code that can be used for error handling
   */
  public readonly code: string;
  
  /**
   * HTTP status code to be used in API responses
   */
  public readonly status: number;
  
  /**
   * Additional error details
   */
  public readonly details?: Record<string, any>;
  
  /**
   * Trace ID for error tracking
   */
  public readonly traceId?: string;
  
  /**
   * Create a new ApplicationError instance
   * 
   * @param message - Error message
   * @param code - Error code
   * @param status - HTTP status code
   * @param details - Additional error details
   * @param traceId - Trace ID for error tracking
   */
  constructor(
    message: string,
    code: string = 'INTERNAL_ERROR',
    status: number = 500,
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.status = status;
    this.details = details;
    this.traceId = traceId || this.generateTraceId();
    
    // Ensure the stack trace includes this constructor
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
  
  /**
   * Convert the error to a plain object for logging or serialization
   * 
   * @returns Plain object representation of the error
   */
  public toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      status: this.status,
      details: this.details,
      traceId: this.traceId,
      stack: this.stack
    };
  }
  
  /**
   * Create an API response object for this error
   * 
   * @returns API response object
   */
  public toResponse(): Record<string, any> {
    return {
      error: {
        code: this.code,
        message: this.message,
        details: this.details,
        trace_id: this.traceId
      }
    };
  }
  
  /**
   * Generate a unique trace ID for the error
   * 
   * @returns Unique trace ID
   */
  private generateTraceId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}