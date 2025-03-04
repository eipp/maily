/**
 * Error handler for HTTP client errors
 * 
 * This module provides utilities for handling errors from HTTP clients like axios or fetch.
 */

import { 
  ApplicationError,
  BadGatewayError,
  BadRequestError,
  ConflictError,
  ForbiddenError,
  GatewayTimeoutError,
  InternalServerError,
  NotFoundError,
  ServiceUnavailableError,
  TooManyRequestsError,
  UnauthorizedError
} from '../errors';

interface HttpErrorResponse {
  status?: number;
  statusCode?: number;
  response?: {
    status?: number;
    data?: any;
  };
  request?: any;
  message?: string;
  code?: string;
}

/**
 * Handles HTTP errors and converts them to appropriate ApplicationError subclasses
 */
export function handleHttpError(error: unknown): ApplicationError {
  // If it's already an ApplicationError, just return it
  if (error instanceof ApplicationError) {
    return error;
  }

  // Try to extract error details from the error object
  const httpError = error as HttpErrorResponse;
  
  // Get the status code from the error
  const statusCode = httpError.statusCode || 
                     httpError.status || 
                     httpError.response?.status || 
                     500;
  
  // Try to extract error details from the response
  let errorDetails;
  let errorMessage = httpError.message || 'An error occurred';
  let errorCode = httpError.code || 'UNKNOWN_ERROR';
  
  if (httpError.response?.data) {
    // Handle structured error responses
    const data = httpError.response.data;
    
    if (typeof data === 'object' && data.error) {
      // Standard error format
      errorMessage = data.error.message || errorMessage;
      errorCode = data.error.code || errorCode;
      errorDetails = data.error.details;
    } else if (typeof data === 'object' && data.message) {
      // Simple error format
      errorMessage = data.message;
      errorCode = data.code || errorCode;
    } else if (typeof data === 'string') {
      // String error message
      errorMessage = data;
    }
  }
  
  // Create an appropriate error based on the status code
  switch (statusCode) {
    case 400:
      return new BadRequestError(errorMessage, errorCode, errorDetails);
    case 401:
      return new UnauthorizedError(errorMessage, errorCode, errorDetails);
    case 403:
      return new ForbiddenError(errorMessage, errorCode, errorDetails);
    case 404:
      return new NotFoundError(errorMessage, errorCode, errorDetails);
    case 409:
      return new ConflictError(errorMessage, errorCode, errorDetails);
    case 429:
      return new TooManyRequestsError(errorMessage);
    case 500:
      return new InternalServerError(errorMessage, errorCode, errorDetails);
    case 502:
      return new BadGatewayError(errorMessage, errorCode, errorDetails);
    case 503:
      return new ServiceUnavailableError(errorMessage, errorCode, errorDetails);
    case 504:
      return new GatewayTimeoutError(errorMessage, errorCode, errorDetails);
    default:
      return new ApplicationError(
        errorMessage,
        errorCode,
        statusCode,
        errorDetails
      );
  }
}

/**
 * Higher-order function that wraps an async function with error handling
 */
export function withErrorHandling<T>(
  fn: (...args: any[]) => Promise<T>,
): (...args: any[]) => Promise<T> {
  return async (...args: any[]): Promise<T> => {
    try {
      return await fn(...args);
    } catch (error) {
      throw handleHttpError(error);
    }
  };
}