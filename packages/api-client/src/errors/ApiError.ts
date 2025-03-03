/**
 * Error thrown when an API request fails with an error response from the server
 */
export class ApiError extends Error {
  /**
   * HTTP status code of the error response
   */
  public readonly status: number;
  
  /**
   * Error response data from the server
   */
  public readonly data: any;
  
  /**
   * Error code (if available in the response)
   */
  public readonly code?: string;
  
  /**
   * Trace ID for error tracking (if available in the response)
   */
  public readonly traceId?: string;
  
  /**
   * Create a new ApiError instance
   * 
   * @param message - Error message
   * @param status - HTTP status code
   * @param data - Error response data
   */
  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.code = data?.error?.code;
    this.traceId = data?.error?.trace_id;
    
    // Ensure the stack trace includes this constructor
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }
  
  /**
   * Check if the error is a validation error (status 400)
   * 
   * @returns True if the error is a validation error
   */
  public isValidationError(): boolean {
    return this.status === 400;
  }
  
  /**
   * Check if the error is an authentication error (status 401)
   * 
   * @returns True if the error is an authentication error
   */
  public isAuthenticationError(): boolean {
    return this.status === 401;
  }
  
  /**
   * Check if the error is an authorization error (status 403)
   * 
   * @returns True if the error is an authorization error
   */
  public isAuthorizationError(): boolean {
    return this.status === 403;
  }
  
  /**
   * Check if the error is a not found error (status 404)
   * 
   * @returns True if the error is a not found error
   */
  public isNotFoundError(): boolean {
    return this.status === 404;
  }
  
  /**
   * Check if the error is a rate limit error (status 429)
   * 
   * @returns True if the error is a rate limit error
   */
  public isRateLimitError(): boolean {
    return this.status === 429;
  }
  
  /**
   * Check if the error is a server error (status 500+)
   * 
   * @returns True if the error is a server error
   */
  public isServerError(): boolean {
    return this.status >= 500;
  }
  
  /**
   * Get validation errors (if available in the response)
   * 
   * @returns Validation errors object or undefined
   */
  public getValidationErrors(): Record<string, string[]> | undefined {
    return this.data?.error?.details?.validation_errors;
  }
}