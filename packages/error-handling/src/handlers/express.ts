/**
 * Express.js error handling middleware
 * 
 * This module provides middleware and error handlers for Express.js applications,
 * standardizing error responses across services.
 */

import { Request, Response, NextFunction, ErrorRequestHandler, Router } from 'express';
import { ZodError } from 'zod';
import { ApplicationError } from '../errors/ApplicationError';
import { ValidationError } from '../errors/ValidationError';

// HTTP error codes mapping
const HTTP_ERROR_CODES: Record<number, string> = {
  400: 'BAD_REQUEST',
  401: 'UNAUTHORIZED',
  403: 'FORBIDDEN',
  404: 'NOT_FOUND',
  409: 'CONFLICT',
  422: 'VALIDATION_ERROR',
  429: 'RATE_LIMIT_EXCEEDED',
  500: 'INTERNAL_SERVER_ERROR',
  502: 'BAD_GATEWAY',
  503: 'SERVICE_UNAVAILABLE',
  504: 'GATEWAY_TIMEOUT'
};

/**
 * Format Zod validation errors into field:messages structure
 */
export function formatZodErrors(error: ZodError): Record<string, string[]> {
  const errors: Record<string, string[]> = {};
  
  error.errors.forEach((issue) => {
    const field = issue.path.join('.');
    
    if (!errors[field]) {
      errors[field] = [];
    }
    
    errors[field].push(issue.message);
  });
  
  return errors;
}

/**
 * Log error details
 */
function logError(
  req: Request, 
  err: Error, 
  traceId: string, 
  details?: Record<string, any>,
  includeStack: boolean = false
): void {
  // Build error log data
  const logData = {
    trace_id: traceId,
    error_type: err.constructor.name,
    error_message: err.message,
    request: {
      method: req.method,
      url: req.url,
      client_ip: req.ip,
      headers: req.headers
    }
  };
  
  // Add details if provided
  if (details) {
    Object.assign(logData, { details });
  }
  
  // Add stack trace for unexpected errors
  if (includeStack) {
    Object.assign(logData, { stack_trace: err.stack });
  }
  
  // Log as error
  console.error('Error handling request:', JSON.stringify(logData));
}

/**
 * Error response middleware for Express.js
 */
export const errorHandler: ErrorRequestHandler = (err, req, res, next) => {
  // Handle ApplicationError instances
  if (err instanceof ApplicationError) {
    // Log error with trace ID
    logError(req, err, err.traceId);
    
    // Return standard error response
    return res.status(err.status).json(err.toResponse());
  }
  
  // Handle Zod validation errors
  if (err instanceof ZodError) {
    // Format validation errors
    const validationErrors = formatZodErrors(err);
    const traceId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Create ValidationError instance
    const validationError = new ValidationError(
      'Validation failed',
      validationErrors,
      traceId
    );
    
    // Log error
    logError(req, err, traceId, { validation_errors: validationErrors });
    
    // Return validation error response
    return res.status(400).json(validationError.toResponse());
  }
  
  // Handle standard Express HTTP errors
  if (err.status || err.statusCode) {
    const statusCode = err.status || err.statusCode || 500;
    const errorCode = HTTP_ERROR_CODES[statusCode] || 'ERROR';
    const traceId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Format error response
    const errorResponse = {
      error: {
        code: errorCode,
        message: err.message || 'An error occurred',
        details: err.details || {},
        trace_id: traceId,
        timestamp: new Date().toISOString()
      }
    };
    
    // Log error
    logError(req, err, traceId);
    
    // Return error response
    return res.status(statusCode).json(errorResponse);
  }
  
  // Handle unexpected errors
  const traceId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Format error response
  const errorResponse = {
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected error occurred',
      trace_id: traceId,
      timestamp: new Date().toISOString()
    }
  };
  
  // Log error with stack trace
  logError(req, err, traceId, undefined, true);
  
  // Return error response
  return res.status(500).json(errorResponse);
};

/**
 * Middleware to initialize request tracing
 */
export function traceMiddleware(req: Request, res: Response, next: NextFunction): void {
  // Generate trace ID
  const traceId = `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Add trace ID to request
  (req as any).traceId = traceId;
  
  // Add trace ID to response headers
  res.setHeader('X-Trace-ID', traceId);
  
  next();
}

/**
 * Not found handler middleware
 */
export function notFoundHandler(req: Request, res: Response): void {
  const traceId = (req as any).traceId || `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Format error response
  const errorResponse = {
    error: {
      code: 'NOT_FOUND',
      message: `Route not found: ${req.method} ${req.url}`,
      trace_id: traceId,
      timestamp: new Date().toISOString()
    }
  };
  
  res.status(404).json(errorResponse);
}

/**
 * Set up error handling for an Express router or app
 */
export function setupErrorHandling(router: Router): void {
  // Add trace middleware
  router.use(traceMiddleware);
  
  // Add 404 handler (should be added after all routes)
  router.use(notFoundHandler);
  
  // Add error handler (should be added last)
  router.use(errorHandler);
}

/**
 * Asynchronous route handler wrapper
 * Automatically catches errors and passes them to the error middleware
 */
export function asyncHandler(fn: (req: Request, res: Response, next: NextFunction) => Promise<any>) {
  return (req: Request, res: Response, next: NextFunction): void => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}