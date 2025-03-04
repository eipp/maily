import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ApplicationError } from '../errors/ApplicationError';

interface ErrorBoundaryProps {
  /**
   * The component to render when an error occurs
   */
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  
  /**
   * A function to be called when an error is caught
   */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  
  /**
   * The children to be rendered
   */
  children: ReactNode;
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
 * A component that catches JavaScript errors in its child component tree,
 * displays a fallback UI, and logs the errors.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    
    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Reset the error state
   */
  resetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // If a custom fallback component was provided, use it
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      // Otherwise, render a default error UI
      return (
        <div className="error-boundary">
          <h2>Something went wrong.</h2>
          <details>
            <summary>Error Details</summary>
            <p>{this.state.error?.toString()}</p>
            {this.state.error instanceof ApplicationError && (
              <p>
                Error Code: {(this.state.error as ApplicationError).code} <br />
                Status: {(this.state.error as ApplicationError).statusCode}
              </p>
            )}
          </details>
          <button
            onClick={this.resetError}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#0070f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Try again
          </button>
        </div>
      );
    }

    // If there's no error, render the children
    return this.props.children;
  }
}

/**
 * A hook that creates an error boundary for a component
 */
export function withErrorBoundary<P>(
  Component: React.ComponentType<P>,
  options: Omit<ErrorBoundaryProps, 'children'> = {}
): React.ComponentType<P> {
  const displayName = Component.displayName || Component.name || 'Component';

  function WithErrorBoundary(props: P): JSX.Element {
    return (
      <ErrorBoundary {...options}>
        <Component {...props} />
      </ErrorBoundary>
    );
  }

  WithErrorBoundary.displayName = `withErrorBoundary(${displayName})`;
  return WithErrorBoundary;
}