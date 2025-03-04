import React from 'react';
import { ApplicationError } from '../errors/ApplicationError';
import { HTTP_STATUS_TO_ERROR_TYPE } from '../errors/ErrorTypes';

interface ErrorFallbackProps {
  /**
   * The error that was caught
   */
  error: Error;
  
  /**
   * A function to reset the error state
   */
  resetError: () => void;
  
  /**
   * Whether to show detailed error information
   */
  showDetails?: boolean;
}

/**
 * A component that renders a user-friendly error message
 */
export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetError,
  showDetails = false,
}) => {
  const isAppError = error instanceof ApplicationError;
  
  // Get the appropriate error message and status
  const message = error.message || 'An unexpected error occurred';
  const statusCode = isAppError ? (error as ApplicationError).statusCode : 500;
  const errorType = HTTP_STATUS_TO_ERROR_TYPE[statusCode] || 'Error';
  const errorCode = isAppError ? (error as ApplicationError).code : 'UNKNOWN_ERROR';

  return (
    <div className="error-fallback">
      <div className="error-fallback-content">
        <h2>{errorType}</h2>
        <p>{message}</p>
        
        {showDetails && (
          <details>
            <summary>Technical Details</summary>
            <div className="error-details">
              <p>Error Code: {errorCode}</p>
              {isAppError && (error as ApplicationError).details && (
                <pre>
                  {JSON.stringify((error as ApplicationError).details, null, 2)}
                </pre>
              )}
              <p>Status Code: {statusCode}</p>
            </div>
          </details>
        )}
        
        <button
          onClick={resetError}
          className="error-reset-button"
        >
          Try Again
        </button>
      </div>
    </div>
  );
};

/**
 * A more detailed error fallback for development environments
 */
export const DevelopmentErrorFallback: React.FC<ErrorFallbackProps> = (props) => {
  return <ErrorFallback {...props} showDetails={true} />;
};

/**
 * A simple error fallback for production environments
 */
export const ProductionErrorFallback: React.FC<ErrorFallbackProps> = (props) => {
  return <ErrorFallback {...props} showDetails={false} />;
};