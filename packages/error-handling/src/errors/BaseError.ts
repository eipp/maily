/**
 * Base error class for the application
 * 
 * This class serves as the base for all application errors and provides
 * standard structure for error handling.
 */
export class BaseError extends Error {
  /** Unique error code */
  public readonly code: string;
  
  /** HTTP status code (if applicable) */
  public readonly statusCode?: number;
  
  /** Additional error details */
  public readonly details?: Record<string, any>;
  
  /** Error severity level */
  public readonly severity: 'fatal' | 'error' | 'warning' | 'info';
  
  /** Whether the error should be retried */
  public readonly retryable: boolean;
  
  /** Whether the error should be reported to monitoring */
  public readonly reportable: boolean;
  
  /** Whether the error details should be exposed to clients */
  public readonly exposable: boolean;

  /**
   * Create a new BaseError
   * 
   * @param message - Error message
   * @param options - Error options
   */
  constructor(message: string, options?: {
    code?: string;
    statusCode?: number;
    details?: Record<string, any>;
    severity?: 'fatal' | 'error' | 'warning' | 'info';
    retryable?: boolean;
    reportable?: boolean;
    exposable?: boolean;
    cause?: Error;
  }) {
    super(message);
    
    // Set the prototype explicitly
    Object.setPrototypeOf(this, BaseError.prototype);
    
    // Set name for better stack traces
    this.name = this.constructor.name;
    
    // Set default and override properties
    this.code = options?.code || 'UNKNOWN_ERROR';
    this.statusCode = options?.statusCode;
    this.details = options?.details;
    this.severity = options?.severity || 'error';
    this.retryable = options?.retryable ?? false;
    this.reportable = options?.reportable ?? true;
    this.exposable = options?.exposable ?? false;
    
    // Capture the cause if provided (Node.js v16.9.0+)
    if (options?.cause && 'cause' in Error) {
      Object.defineProperty(this, 'cause', {
        value: options.cause,
        enumerable: false,
        writable: true,
        configurable: true
      });
    }
    
    // Capture stack trace
    Error.captureStackTrace(this, this.constructor);
  }

  /**
   * Convert the error to a plain JSON object for logging or serialization
   */
  public toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      details: this.details,
      severity: this.severity,
      stack: this.stack,
      cause: (this as any).cause ? 
        ((this as any).cause instanceof Error && (this as any).cause.toJSON) ? 
          (this as any).cause.toJSON() : 
          String((this as any).cause) : 
        undefined
    };
  }

  /**
   * Create a client-safe version of the error
   */
  public toClientError(): Record<string, any> {
    return {
      message: this.exposable ? this.message : 'An error occurred',
      code: this.code,
      ...(this.exposable && this.details ? { details: this.details } : {}),
      ...(this.statusCode ? { statusCode: this.statusCode } : {})
    };
  }
}

export default BaseError;