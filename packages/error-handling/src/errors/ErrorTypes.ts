/**
 * Standard error codes for the application
 */
export enum ErrorCode {
  // General errors
  INTERNAL_ERROR = 'internal_error',
  VALIDATION_ERROR = 'validation_error',
  NOT_FOUND = 'not_found',
  ALREADY_EXISTS = 'already_exists',
  UNAUTHORIZED = 'unauthorized',
  FORBIDDEN = 'forbidden',
  BAD_REQUEST = 'bad_request',
  CONFLICT = 'conflict',
  TOO_MANY_REQUESTS = 'too_many_requests',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  
  // Domain-specific errors
  CAMPAIGN_ERROR = 'campaign_error',
  TEMPLATE_ERROR = 'template_error',
  CONTACT_ERROR = 'contact_error',
  AI_ERROR = 'ai_error',
  MODEL_ERROR = 'model_error',
  INTEGRATION_ERROR = 'integration_error',
  BLOCKCHAIN_ERROR = 'blockchain_error',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',
  DATA_PROCESSING_ERROR = 'data_processing_error',
  CONFIGURATION_ERROR = 'configuration_error',
  QUOTA_EXCEEDED = 'quota_exceeded',
  FEATURE_DISABLED = 'feature_disabled',
  NETWORK_ERROR = 'network_error',
  TIMEOUT_ERROR = 'timeout_error',
  CONTENT_FILTER_ERROR = 'content_filter_error',
}

/**
 * Interface for error detail information
 */
export interface ErrorDetail {
  /**
   * Error code for the specific detail
   */
  code: string;
  
  /**
   * Human-readable message for the error detail
   */
  message: string;
  
  /**
   * Optional field name if the error is related to a specific field
   */
  field?: string;
  
  /**
   * Additional error information
   */
  info?: Record<string, any>;
}

/**
 * Standard error response format
 */
export interface ErrorResponse {
  /**
   * Flag indicating this is an error response
   */
  error: boolean;
  
  /**
   * Error code for categorizing the error
   */
  error_code: string;
  
  /**
   * Human-readable error message
   */
  message: string;
  
  /**
   * HTTP status code
   */
  status_code: number;
  
  /**
   * Unique trace ID for error tracking
   */
  trace_id: string;
  
  /**
   * Timestamp when the error occurred
   */
  timestamp: number;
  
  /**
   * Request ID if available
   */
  request_id?: string;
  
  /**
   * Detailed error information
   */
  details?: ErrorDetail[];
  
  /**
   * URL to error documentation
   */
  documentation_url?: string;
}