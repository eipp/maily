import { ApplicationError } from './ApplicationError';

/**
 * Error thrown when validation fails
 */
export class ValidationError extends ApplicationError {
  /**
   * Validation errors by field
   */
  public readonly validationErrors: Record<string, string[]>;
  
  /**
   * Create a new ValidationError instance
   * 
   * @param message - Error message
   * @param validationErrors - Validation errors by field
   * @param traceId - Trace ID for error tracking
   */
  constructor(
    message: string = 'Validation failed',
    validationErrors: Record<string, string[]> = {},
    traceId?: string
  ) {
    super(
      message,
      'VALIDATION_ERROR',
      400,
      { validation_errors: validationErrors },
      traceId
    );
    
    this.validationErrors = validationErrors;
  }
  
  /**
   * Add a validation error for a field
   * 
   * @param field - Field name
   * @param error - Error message
   * @returns This instance for method chaining
   */
  public addError(field: string, error: string): ValidationError {
    if (!this.validationErrors[field]) {
      this.validationErrors[field] = [];
    }
    
    this.validationErrors[field].push(error);
    
    // Also update the details object
    if (this.details && this.details.validation_errors) {
      this.details.validation_errors = { ...this.validationErrors };
    }
    
    return this;
  }
  
  /**
   * Check if there are any validation errors
   * 
   * @returns True if there are validation errors
   */
  public hasErrors(): boolean {
    return Object.keys(this.validationErrors).length > 0;
  }
  
  /**
   * Get the validation errors for a field
   * 
   * @param field - Field name
   * @returns Array of error messages
   */
  public getFieldErrors(field: string): string[] {
    return this.validationErrors[field] || [];
  }
  
  /**
   * Create a validation error from a Zod validation result
   * 
   * @param zodError - Zod validation error
   * @returns Validation error instance
   */
  public static fromZodError(zodError: any): ValidationError {
    const validationErrors: Record<string, string[]> = {};
    
    for (const issue of zodError.errors) {
      const field = issue.path.join('.');
      
      if (!validationErrors[field]) {
        validationErrors[field] = [];
      }
      
      validationErrors[field].push(issue.message);
    }
    
    return new ValidationError('Validation failed', validationErrors);
  }
}