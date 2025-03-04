/**
 * React Error Boundary Component
 * 
 * This module provides a reusable Error Boundary component for React applications,
 * standardizing error handling in the UI.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  /**
   * Custom fallback component or function to render when an error occurs
   */
  fallback?: ReactNode | ((error: Error, errorInfo: ErrorInfo) => ReactNode);
  
  /**
   * Component children
   */
  children: ReactNode;
  
  /**
   * Function to call when an error is caught
   */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  
  /**
   * Reset error state when a key changes
   */
  resetKeys?: any[];
}

interface ErrorBoundaryState {
  /**
   * Whether an error has been caught
   */
  hasError: boolean;
  
  /**
   * The error that was caught
   */
  error: Error | null;
  
  /**
   * Error info object from React
   */
  errorInfo: ErrorInfo | null;
}

/**
 * Default fallback component displayed when an error occurs
 */
function DefaultFallback({ error }: { error: Error | null }) {
  return (
    <div className="error-boundary-fallback">
      <h2>Something went wrong</h2>
      <details>
        <summary>Error details</summary>
        <pre>{error?.toString() || 'Unknown error'}</pre>
      </details>
    </div>
  );
}

/**
 * Error Boundary component for catching and handling errors in React components
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }
  
  /**
   * Called when an error is thrown in a child component
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }
  
  /**
   * Called after an error is thrown in a child component
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Update state with error info
    this.setState({
      errorInfo
    });
    
    // Call error callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // Log error to console in development
    if (process.env.NODE_ENV !== 'production') {
      console.error('Error caught by ErrorBoundary:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }
  }
  
  /**
   * Reset error state when resetKeys change
   */
  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (
      this.state.hasError &&
      this.props.resetKeys &&
      this.props.resetKeys.some((key, i) => key !== prevProps.resetKeys?.[i])
    ) {
      this.reset();
    }
  }
  
  /**
   * Reset error state
   */
  reset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };
  
  render(): ReactNode {
    // Return children if no error
    if (!this.state.hasError) {
      return this.props.children;
    }
    
    // Render fallback
    if (this.props.fallback) {
      // If fallback is a function, call it with error and errorInfo
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback(
          this.state.error as Error,
          this.state.errorInfo as ErrorInfo
        );
      }
      
      // Otherwise, render the fallback component
      return this.props.fallback;
    }
    
    // Render default fallback
    return <DefaultFallback error={this.state.error} />;
  }
}

/**
 * Higher-order component to wrap a component with an ErrorBoundary
 */
export function withErrorBoundary<P>(
  Component: React.ComponentType<P>,
  errorBoundaryProps: Omit<ErrorBoundaryProps, 'children'>
): React.ComponentType<P> {
  const WithErrorBoundary = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  // Set display name for debugging
  const componentName = Component.displayName || Component.name || 'Component';
  WithErrorBoundary.displayName = `WithErrorBoundary(${componentName})`;
  
  return WithErrorBoundary;
}