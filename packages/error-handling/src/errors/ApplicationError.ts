import { ErrorCode, ErrorDetail, ErrorResponse } from './ErrorTypes';

/**
 * Base error class for all application errors
 */
export class ApplicationError extends Error {
  /**
   * Error code that can be used for error handling
   */
  public readonly errorCode: ErrorCode | string;
  
  /**
   * HTTP status code to be used in API responses
   */
  public readonly statusCode: number;
  
  /**
   * Additional error details
   */
  public readonly details: ErrorDetail[];
  
  /**
   * Trace ID for error tracking
   */
  public readonly traceId: string;
  
  /**
   * Request ID if available
   */
  public readonly requestId?: string;
  
  /**
   * Provider information (e.g., API provider)
   */
  public readonly provider?: string;
  
  /**
   * Timestamp when the error occurred
   */
  public readonly timestamp: number;
  
  /**
   * Base URL for error documentation
   */
  protected readonly documentationUrlBase: string = 'https://docs.maily.com/errors';
  
  /**
   * Create a new ApplicationError instance
   * 
   * @param message - Error message
   * @param errorCode - Error code from ErrorCode enum or string
   * @param statusCode - HTTP status code
   * @param details - Error details as array of ErrorDetail objects or single object
   * @param traceId - Trace ID for error tracking
   * @param requestId - Request ID if available
   * @param provider - Provider information (e.g., API provider)
   */
  constructor(
    message: string,
    errorCode: ErrorCode | string = ErrorCode.INTERNAL_ERROR,
    statusCode: number = 500,
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(message);
    this.name = this.constructor.name;
    this.errorCode = errorCode;
    this.statusCode = statusCode;
    this.timestamp = Date.now();
    this.traceId = traceId || this.generateTraceId();
    this.requestId = requestId;
    this.provider = provider;
    
    // Process details
    if (!details) {
      this.details = [];
    } else if (Array.isArray(details)) {
      this.details = details;
    } else {
      this.details = [{
        code: `${this.errorCode}.details`,
        message: 'Error details',
        info: details
      }];
    }
    
    // Ensure the stack trace includes this constructor
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
    
    // Log the error
    this.logError();
  }
  
  /**
   * Log the error to the console with appropriate level
   */
  protected logError(): void {
    const context = {
      errorType: this.name,
      errorCode: this.errorCode,
      traceId: this.traceId,
      statusCode: this.statusCode
    };
    
    if (this.statusCode >= 500) {
      console.error(`[ERROR] ${this.errorCode}: ${this.message}`, context);
    } else {
      console.warn(`[WARN] ${this.errorCode}: ${this.message}`, context);
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
      errorCode: this.errorCode,
      statusCode: this.statusCode,
      details: this.details,
      traceId: this.traceId,
      requestId: this.requestId,
      provider: this.provider,
      timestamp: this.timestamp,
      stack: this.stack
    };
  }
  
  /**
   * Create a standardized error response object
   * 
   * @returns Standardized error response
   */
  public toResponse(): ErrorResponse {
    const response: ErrorResponse = {
      error: true,
      error_code: this.errorCode.toString(),
      message: this.message,
      status_code: this.statusCode,
      trace_id: this.traceId,
      timestamp: this.timestamp,
      documentation_url: `${this.documentationUrlBase}/${this.errorCode}`
    };
    
    if (this.requestId) {
      response.request_id = this.requestId;
    }
    
    if (this.details && this.details.length > 0) {
      response.details = this.details;
    }
    
    return response;
  }
  
  /**
   * Generate a unique trace ID for the error
   * 
   * @returns Unique trace ID
   */
  private generateTraceId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
  
  /**
   * Create an ApplicationError from another error
   * 
   * @param error - Original error
   * @param options - Additional options
   * @returns New ApplicationError instance
   */
  public static fromError(
    error: Error, 
    options: {
      errorCode?: ErrorCode | string,
      statusCode?: number,
      details?: ErrorDetail[] | Record<string, any>,
      traceId?: string,
      requestId?: string,
      provider?: string
    } = {}
  ): ApplicationError {
    return new ApplicationError(
      error.message || 'An unknown error occurred',
      options.errorCode || ErrorCode.INTERNAL_ERROR,
      options.statusCode || 500,
      options.details || { originalError: error.toString(), stack: error.stack },
      options.traceId,
      options.requestId,
      options.provider
    );
  }
}