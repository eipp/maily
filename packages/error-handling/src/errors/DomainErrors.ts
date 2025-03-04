/**
 * Domain-specific error classes
 * 
 * These classes represent errors specific to the business domain of the application.
 * They provide more context than generic HTTP errors and should be used when 
 * handling application-specific errors.
 */

import { ApplicationError } from './ApplicationError';

/**
 * User-related errors
 */
export class UserError extends ApplicationError {
  constructor(
    message: string,
    code: string = 'USER_ERROR',
    statusCode: number = 400,
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, statusCode, details, traceId);
  }
}

export class UserNotFoundError extends UserError {
  constructor(
    userId: string,
    message: string = `User not found`,
    traceId?: string
  ) {
    super(
      message,
      'USER_NOT_FOUND',
      404,
      { userId },
      traceId
    );
  }
}

/**
 * Authentication-related errors
 */
export class AuthenticationError extends ApplicationError {
  constructor(
    message: string = 'Authentication failed',
    code: string = 'AUTHENTICATION_FAILED',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 401, details, traceId);
  }
}

export class InvalidCredentialsError extends AuthenticationError {
  constructor(
    message: string = 'Invalid username or password',
    traceId?: string
  ) {
    super(message, 'INVALID_CREDENTIALS', undefined, traceId);
  }
}

export class TokenExpiredError extends AuthenticationError {
  constructor(
    message: string = 'Authentication token has expired',
    traceId?: string
  ) {
    super(message, 'TOKEN_EXPIRED', undefined, traceId);
  }
}

/**
 * Authorization-related errors
 */
export class AuthorizationError extends ApplicationError {
  constructor(
    message: string = 'Access denied',
    code: string = 'ACCESS_DENIED',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, 403, details, traceId);
  }
}

export class InsufficientPermissionsError extends AuthorizationError {
  constructor(
    resource: string,
    action: string,
    message?: string,
    traceId?: string
  ) {
    const errorMessage = message || `Insufficient permissions to ${action} ${resource}`;
    super(
      errorMessage,
      'INSUFFICIENT_PERMISSIONS',
      { resource, action },
      traceId
    );
  }
}

/**
 * Campaign-related errors
 */
export class CampaignError extends ApplicationError {
  constructor(
    message: string,
    code: string = 'CAMPAIGN_ERROR',
    statusCode: number = 400,
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, statusCode, details, traceId);
  }
}

export class CampaignNotFoundError extends CampaignError {
  constructor(
    campaignId: string,
    message: string = `Campaign not found`,
    traceId?: string
  ) {
    super(
      message,
      'CAMPAIGN_NOT_FOUND',
      404,
      { campaignId },
      traceId
    );
  }
}

export class CampaignAlreadyExistsError extends CampaignError {
  constructor(
    name: string,
    message?: string,
    traceId?: string
  ) {
    const errorMessage = message || `Campaign with name '${name}' already exists`;
    super(
      errorMessage,
      'CAMPAIGN_ALREADY_EXISTS',
      409,
      { name },
      traceId
    );
  }
}

/**
 * Template-related errors
 */
export class TemplateError extends ApplicationError {
  constructor(
    message: string,
    code: string = 'TEMPLATE_ERROR',
    statusCode: number = 400,
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, statusCode, details, traceId);
  }
}

export class TemplateNotFoundError extends TemplateError {
  constructor(
    templateId: string,
    message: string = `Template not found`,
    traceId?: string
  ) {
    super(
      message,
      'TEMPLATE_NOT_FOUND',
      404,
      { templateId },
      traceId
    );
  }
}

export class TemplateRenderingError extends TemplateError {
  constructor(
    templateId: string,
    details: Record<string, any>,
    message: string = `Failed to render template`,
    traceId?: string
  ) {
    super(
      message,
      'TEMPLATE_RENDERING_ERROR',
      500,
      {
        templateId,
        ...details
      },
      traceId
    );
  }
}

/**
 * AI/ML-related errors
 */
export class AIError extends ApplicationError {
  constructor(
    message: string,
    code: string = 'AI_ERROR',
    statusCode: number = 500,
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(message, code, statusCode, details, traceId);
  }
}

export class ModelNotAvailableError extends AIError {
  constructor(
    modelId: string,
    message?: string,
    traceId?: string
  ) {
    const errorMessage = message || `AI model '${modelId}' is not available`;
    super(
      errorMessage,
      'MODEL_NOT_AVAILABLE',
      503,
      { modelId },
      traceId
    );
  }
}

export class ContentModerationError extends AIError {
  constructor(
    message: string = 'Content failed moderation checks',
    details?: Record<string, any>,
    traceId?: string
  ) {
    super(
      message,
      'CONTENT_MODERATION_ERROR',
      400,
      details,
      traceId
    );
  }
}