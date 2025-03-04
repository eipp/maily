import { useState, useCallback } from 'react';
import { ApplicationError, NetworkError, TimeoutError } from '../errors';

interface ErrorState {
  /** Whether there is an error */
  hasError: boolean;
  /** The error message */
  message: string;
  /** The error object */
  error: Error | null;
}

interface ErrorHandlerOptions {
  /** Whether to automatically reset the error after a delay */
  autoReset?: boolean;
  /** Delay in ms before auto-resetting the error */
  resetDelay?: number;
  /** Called when an error occurs */
  onError?: (error: Error) => void;
}

/**
 * Hook for standardized error handling
 */
export function useErrorHandler(options: ErrorHandlerOptions = {}) {
  const { 
    autoReset = false, 
    resetDelay = 5000,
    onError 
  } = options;
  
  const [errorState, setErrorState] = useState<ErrorState>({
    hasError: false,
    message: '',
    error: null
  });
  
  /**
   * Handle an error
   */
  const handleError = useCallback((error: unknown) => {
    // Convert to standard ApplicationError
    const appError = error instanceof ApplicationError
      ? error
      : error instanceof Error
        ? ApplicationError.fromError(error)
        : new ApplicationError(
            typeof error === 'string' ? error : 'An unknown error occurred'
          );
    
    // Update error state
    setErrorState({
      hasError: true,
      message: appError.message,
      error: appError
    });
    
    // Call onError callback if provided
    if (onError) {
      onError(appError);
    }
    
    // Auto-reset if enabled
    if (autoReset) {
      setTimeout(() => {
        resetError();
      }, resetDelay);
    }
    
    return appError;
  }, [autoReset, resetDelay, onError]);
  
  /**
   * Reset the error state
   */
  const resetError = useCallback(() => {
    setErrorState({
      hasError: false,
      message: '',
      error: null
    });
  }, []);
  
  /**
   * Wrap an async function with error handling
   */
  const withErrorHandling = useCallback(<T extends any[], R>(
    fn: (...args: T) => Promise<R>
  ) => {
    return async (...args: T): Promise<R> => {
      try {
        return await fn(...args);
      } catch (error) {
        handleError(error);
        throw error;
      }
    };
  }, [handleError]);
  
  /**
   * Execute an API call with standardized error handling
   */
  const executeApiCall = useCallback(async <T>(
    apiCall: () => Promise<T>
  ): Promise<T | null> => {
    try {
      // Reset any previous errors
      resetError();
      
      // Execute the API call
      return await apiCall();
    } catch (error) {
      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        handleError(new NetworkError('Network error. Please check your connection.'));
        return null;
      }
      
      // Handle timeout errors
      if (error instanceof Error && error.name === 'AbortError') {
        handleError(new TimeoutError('Request timed out. Please try again.'));
        return null;
      }
      
      // Handle other errors
      handleError(error);
      return null;
    }
  }, [handleError, resetError]);
  
  return {
    ...errorState,
    handleError,
    resetError,
    withErrorHandling,
    executeApiCall
  };
}