/**
 * Type definitions for error handling
 */

/**
 * Standard error response format
 */
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    statusCode: number;
    details?: Record<string, any>;
    traceId?: string;
  };
}

/**
 * Error codes by category
 */
export enum ErrorCode {
  // Generic errors
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  NOT_IMPLEMENTED = 'NOT_IMPLEMENTED',
  
  // Validation errors
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_REQUEST = 'INVALID_REQUEST',
  INVALID_PARAMETER = 'INVALID_PARAMETER',
  
  // Authentication errors
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  TOKEN_INVALID = 'TOKEN_INVALID',
  
  // Authorization errors
  ACCESS_DENIED = 'ACCESS_DENIED',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',
  
  // Resource errors
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  RESOURCE_ALREADY_EXISTS = 'RESOURCE_ALREADY_EXISTS',
  RESOURCE_CONFLICT = 'RESOURCE_CONFLICT',
  
  // User errors
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  USER_ALREADY_EXISTS = 'USER_ALREADY_EXISTS',
  
  // Campaign errors
  CAMPAIGN_ERROR = 'CAMPAIGN_ERROR',
  CAMPAIGN_NOT_FOUND = 'CAMPAIGN_NOT_FOUND',
  CAMPAIGN_ALREADY_EXISTS = 'CAMPAIGN_ALREADY_EXISTS',
  
  // Template errors
  TEMPLATE_ERROR = 'TEMPLATE_ERROR',
  TEMPLATE_NOT_FOUND = 'TEMPLATE_NOT_FOUND',
  TEMPLATE_RENDERING_ERROR = 'TEMPLATE_RENDERING_ERROR',
  
  // AI/ML errors
  AI_ERROR = 'AI_ERROR',
  MODEL_NOT_AVAILABLE = 'MODEL_NOT_AVAILABLE',
  CONTENT_MODERATION_ERROR = 'CONTENT_MODERATION_ERROR',
  
  // Integration errors
  INTEGRATION_ERROR = 'INTEGRATION_ERROR',
  EXTERNAL_SERVICE_ERROR = 'EXTERNAL_SERVICE_ERROR',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  
  // Database errors
  DATABASE_ERROR = 'DATABASE_ERROR',
  QUERY_ERROR = 'QUERY_ERROR',
  
  // Network errors
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  CONNECTION_ERROR = 'CONNECTION_ERROR',
}

/**
 * Maps HTTP status codes to error types
 */
export const HTTP_STATUS_TO_ERROR_TYPE: Record<number, string> = {
  400: 'Bad Request',
  401: 'Unauthorized',
  403: 'Forbidden',
  404: 'Not Found',
  409: 'Conflict',
  422: 'Validation Error',
  429: 'Too Many Requests',
  500: 'Internal Server Error',
  502: 'Bad Gateway',
  503: 'Service Unavailable',
  504: 'Gateway Timeout',
};