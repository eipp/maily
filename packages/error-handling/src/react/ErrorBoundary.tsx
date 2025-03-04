'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ApplicationError } from '../errors/ApplicationError';

interface ErrorBoundaryProps {
  /**
   * Custom component to display when an error occurs
   */
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  
  /**
   * Children to render
   */
  children?: ReactNode;
  
  /**
   * Called when an error is caught
   */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  
  /**
   * Called when error is reset
   */
  onReset?: () => void;
  
  /**
   * Enable/disable error boundary
   */
  disabled?: boolean;
}

interface ErrorBoundaryState {
  /**
   * Whether an error has been caught
   */
  hasError: boolean;
  
  /**
   * The error that was caught, if any
   */
  error: Error | null;
}

/**
 * Error boundary component for catching and handling React component errors
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { 
      hasError: true,
      error
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console
    console.error("Uncaught error in component:", error, errorInfo);
    
    // Convert to ApplicationError if it's not already
    const appError = error instanceof ApplicationError 
      ? error 
      : new ApplicationError(
          error.message || 'An unexpected error occurred',
          'COMPONENT_ERROR',
          500,
          { 
            componentStack: errorInfo.componentStack,
            originalError: error.toString(),
            stack: error.stack
          }
        );
    
    // Call optional onError callback
    if (this.props.onError) {
      this.props.onError(appError, errorInfo);
    }
    
    // Report error to any analytics/monitoring tools
    this.reportError(appError, errorInfo);
  }
  
  /**
   * Report error to analytics/monitoring
   */
  private reportError(error: Error, errorInfo: ErrorInfo) {
    // Check if window.analytics exists (to avoid throwing in SSR)
    if (typeof window !== 'undefined' && window.analytics) {
      window.analytics.trackError(error, {
        componentStack: errorInfo.componentStack,
      });
    }
  }
  
  /**
   * Reset error state
   */
  private resetErrorState = () => {
    this.setState({ 
      hasError: false,
      error: null
    });
    
    // Call optional onReset callback
    if (this.props.onReset) {
      this.props.onReset();
    }
  }

  public render() {
    // Skip error boundary if disabled
    if (this.props.disabled) {
      return this.props.children;
    }
    
    // Show fallback UI if an error occurred
    if (this.state.hasError) {
      // If fallback is a function, call it with error and reset function
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback(this.state.error!, this.resetErrorState);
      }
      
      // If fallback is a component, return it
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // Otherwise return default error UI
      return (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 m-4 border border-red-100 dark:border-red-900/30">
          <h2 className="text-lg font-semibold text-red-800 dark:text-red-400">Something went wrong</h2>
          <p className="mt-2 text-sm text-red-700 dark:text-red-300">
            An error occurred while rendering this component.
          </p>
          <details className="mt-2">
            <summary className="text-sm cursor-pointer text-red-600 dark:text-red-400 hover:underline">
              Error details
            </summary>
            <pre className="mt-2 text-xs p-2 bg-red-100 dark:bg-red-900/40 overflow-auto rounded border border-red-200 dark:border-red-900/50">
              {this.state.error?.toString()}
            </pre>
          </details>
          <button
            onClick={this.resetErrorState}
            className="mt-4 px-3 py-1 text-sm bg-red-100 dark:bg-red-900/50 hover:bg-red-200 dark:hover:bg-red-900/70 text-red-700 dark:text-red-200 rounded-md transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }

    // Otherwise, render children normally
    return this.props.children;
  }
}

// Add window.analytics type definition
declare global {
  interface Window {
    analytics?: {
      trackError: (error: Error, metadata?: Record<string, any>) => void;
    };
  }
}