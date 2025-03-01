00/**
 * Lazy Loading Utilities
 *
 * This module provides utilities for optimized component loading,
 * including React.lazy integration, error boundaries, and loading states.
 */

import React, { Suspense, lazy, ComponentType } from 'react';
import dynamic from 'next/dynamic';

/**
 * Error boundary component for lazy-loaded components
 */
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error in lazy-loaded component:', error, errorInfo);

    // Log to monitoring service if available
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(error);
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

/**
 * Default loading component
 */
const DefaultLoading: React.FC = () => (
  <div className="flex justify-center items-center p-4 min-h-[100px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
  </div>
);

/**
 * Default error fallback component
 */
const DefaultError: React.FC = () => (
  <div className="p-4 text-center text-red-500 border border-red-200 rounded bg-red-50">
    <p>Failed to load component. Please try refreshing the page.</p>
  </div>
);

/**
 * Options for lazy loading a component
 */
interface LazyLoadOptions {
  loading?: React.ReactNode;
  errorFallback?: React.ReactNode;
  ssr?: boolean;
  suspense?: boolean;
}

/**
 * Load a component lazily with error handling and loading state
 *
 * @param factory Function that imports the component
 * @param options Configuration options
 * @returns Lazy-loaded component
 *
 * @example
 * // Basic usage
 * const LazyComponent = lazyLoad(() => import('../components/HeavyComponent'));
 *
 * // With custom loading and error states
 * const LazyComponent = lazyLoad(() => import('../components/HeavyComponent'), {
 *   loading: <CustomSpinner />,
 *   errorFallback: <ErrorMessage />,
 *   ssr: false // Disable server-side rendering
 * });
 */
export function lazyLoad<T extends ComponentType<any>>(
  factory: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): React.ComponentType<React.ComponentProps<T>> {
  const {
    loading = <DefaultLoading />,
    errorFallback = <DefaultError />,
    ssr = true,
    suspense = true,
  } = options;

  // For Next.js dynamic imports
  if (!suspense) {
    return dynamic(factory, {
      loading: () => <>{loading}</>,
      ssr,
    });
  }

  // For React.lazy
  const LazyComponent = lazy(factory);

  const WrappedComponent: React.FC<React.ComponentProps<T>> = (props) => (
    <ErrorBoundary fallback={<>{errorFallback}</>}>
      <Suspense fallback={<>{loading}</>}>
        <LazyComponent {...props} />
      </Suspense>
    </ErrorBoundary>
  );

  // Set display name for easier debugging
  const getComponentName = () => {
    return factory.toString().match(/import\(['"](.+?)['"]\)/)?.[1] || 'LazyComponent';
  };

  WrappedComponent.displayName = `Lazy(${getComponentName()})`;

  return WrappedComponent;
}

/**
 * Prefetch a component to improve perceived performance
 *
 * @param factory Function that imports the component
 *
 * @example
 * // Prefetch a component on mouse hover
 * <div onMouseEnter={() => prefetchComponent(() => import('../components/HeavyComponent'))}>
 *   Hover me to prefetch
 * </div>
 */
export function prefetchComponent(factory: () => Promise<any>): void {
  if (typeof window === 'undefined') return;

  // Create a lightweight preloader that doesn't block rendering
  const preloader = () => {
    factory()
      .then(() => {
        console.log(`Prefetched component: ${factory.toString()}`);
      })
      .catch((error) => {
        console.error(`Failed to prefetch component: ${error}`);
      });
  };

  // Use requestIdleCallback for better performance if available
  if (window.requestIdleCallback) {
    window.requestIdleCallback(preloader, { timeout: 2000 });
  } else {
    setTimeout(preloader, 0);
  }
}

/**
 * Facade for creating a lazy-loadable route component
 *
 * @param factory Function that imports the component
 * @returns Lazy-loaded route component
 *
 * @example
 * // In your routes file
 * const Dashboard = lazyRoute(() => import('../pages/Dashboard'));
 */
export function lazyRoute<T extends ComponentType<any>>(
  factory: () => Promise<{ default: T }>
): React.ComponentType<React.ComponentProps<T>> {
  return lazyLoad(factory, {
    loading: (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    ),
    ssr: true,
  });
}

/**
 * Facade for creating lazy-loadable modal components
 *
 * @param factory Function that imports the component
 * @returns Lazy-loaded modal component
 *
 * @example
 * // In your component
 * const SettingsModal = lazyModal(() => import('../modals/SettingsModal'));
 */
export function lazyModal<T extends ComponentType<any>>(
  factory: () => Promise<{ default: T }>
): React.ComponentType<React.ComponentProps<T>> {
  return lazyLoad(factory, {
    loading: (
      <div className="flex justify-center items-center min-h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    ),
    ssr: false, // Modals typically don't need SSR
  });
}

/**
 * Type definition for Next.js window to include Sentry
 */
declare global {
  interface Window {
    Sentry?: {
      captureException: (error: Error) => void;
    };
  }
}
