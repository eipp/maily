import { ApplicationError } from './ApplicationError';
import { ErrorCode, ErrorDetail } from './ErrorTypes';
import { NotFoundError, ServerError } from './HttpErrors';

/**
 * Base class for AI-related errors
 */
export class AIError extends ApplicationError {
  constructor(
    message: string = 'AI service error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.AI_ERROR,
      500,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for AI model errors
 */
export class AIModelError extends AIError {
  constructor(
    message: string = 'AI model error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.MODEL_ERROR;
  }
}

/**
 * Error for integration errors
 */
export class IntegrationError extends ApplicationError {
  constructor(
    message: string = 'Integration error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.INTEGRATION_ERROR,
      500,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for database errors
 */
export class DatabaseError extends ApplicationError {
  constructor(
    message: string = 'Database error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string
  ) {
    super(
      message,
      ErrorCode.DATA_PROCESSING_ERROR,
      500,
      details,
      traceId,
      requestId
    );
  }
}

/**
 * Error for blockchain errors
 */
export class BlockchainError extends ApplicationError {
  constructor(
    message: string = 'Blockchain error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.BLOCKCHAIN_ERROR,
      500,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for configuration errors
 */
export class ConfigurationError extends ApplicationError {
  constructor(
    message: string = 'Configuration error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string
  ) {
    super(
      message,
      ErrorCode.CONFIGURATION_ERROR,
      500,
      details,
      traceId,
      requestId
    );
  }
}

/**
 * Error for quota exceeded
 */
export class QuotaExceededError extends ApplicationError {
  constructor(
    message: string = 'Quota exceeded',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.QUOTA_EXCEEDED,
      402,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for network errors
 */
export class NetworkError extends ApplicationError {
  constructor(
    message: string = 'Network error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.NETWORK_ERROR,
      503,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for timeout errors
 */
export class TimeoutError extends ApplicationError {
  constructor(
    message: string = 'Request timed out',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.TIMEOUT_ERROR,
      504,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for content filter errors
 */
export class ContentFilterError extends ApplicationError {
  constructor(
    message: string = 'Content filtered',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      ErrorCode.CONTENT_FILTER_ERROR,
      400,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for unavailable AI models
 */
export class ModelUnavailableError extends AIError {
  constructor(
    message: string = 'Model is currently unavailable',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.SERVICE_UNAVAILABLE;
    this.statusCode = 503;
  }
}

/**
 * Error for overloaded AI models
 */
export class ModelOverloadedError extends ModelUnavailableError {
  constructor(
    message: string = 'Model is currently overloaded',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
  }
}

/**
 * Error for unsupported AI models
 */
export class UnsupportedModelError extends AIError {
  constructor(
    message: string = 'Model is not supported',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId,
      provider
    );
    this.errorCode = ErrorCode.BAD_REQUEST;
    this.statusCode = 400;
  }
}

/**
 * Error for campaign not found
 */
export class CampaignNotFoundError extends NotFoundError {
  constructor(
    message: string = 'Campaign not found',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId
    );
    this.errorCode = ErrorCode.CAMPAIGN_ERROR;
  }
}

/**
 * Error for template not found
 */
export class TemplateNotFoundError extends NotFoundError {
  constructor(
    message: string = 'Template not found',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId
    );
    this.errorCode = ErrorCode.TEMPLATE_ERROR;
  }
}

/**
 * Error for contact not found
 */
export class ContactNotFoundError extends NotFoundError {
  constructor(
    message: string = 'Contact not found',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string
  ) {
    super(
      message,
      details,
      traceId,
      requestId
    );
    this.errorCode = ErrorCode.CONTACT_ERROR;
  }
}

/**
 * Legacy compatibility class
 */
export class ConsentNotFoundError extends NotFoundError {
  constructor(
    message: string = 'Consent record not found',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string
  ) {
    super(message, details, traceId, requestId);
  }
}

/**
 * Legacy compatibility class
 */
export class ExternalServiceError extends IntegrationError {
  constructor(
    message: string = 'External service error',
    details?: ErrorDetail[] | Record<string, any>,
    traceId?: string,
    requestId?: string,
    provider?: string
  ) {
    super(message, details, traceId, requestId, provider);
  }
}