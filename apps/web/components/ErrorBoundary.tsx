'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { analytics } from '../utils/analytics';

interface Props {
  fallback?: ReactNode;
  children?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { 
      hasError: true,
      error
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    
    // Track error with analytics
    analytics.trackError(error, {
      componentStack: errorInfo.componentStack,
    });
    
    // Call optional onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
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
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-3 py-1 text-sm bg-red-100 dark:bg-red-900/50 hover:bg-red-200 dark:hover:bg-red-900/70 text-red-700 dark:text-red-200 rounded-md transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
