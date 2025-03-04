// Export standardized error handling modules
export * from './errors';
export * from './react';

// Legacy exports for backward compatibility
// These will be removed in a future version

// Legacy Error classes
export * from './errors/ApplicationError';
// No need to export ValidationError, etc. as they're included in ./errors

// Legacy Error handlers
export * from './handlers/errorHandler';
export * from './handlers/apiErrorHandler';
export * from './handlers/validateErrorHandler';
export * from './handlers/reactErrorHandler';

// Legacy Error utilities
export * from './utils/errorCode';
export * from './utils/errorLogger';
export * from './utils/zodErrorFormatter';
export * from './utils/errorReporter';