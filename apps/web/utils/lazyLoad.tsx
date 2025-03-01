import React, { lazy, Suspense } from 'react';

interface LazyLoadOptions {
  /**
   * Minimum delay in milliseconds before showing the component.
   * This can help prevent layout shifts for very fast loads.
   */
  minDelay?: number;

  /**
   * Fallback component to show while loading.
   */
  fallback?: React.ReactNode;
}

/**
 * Default loading component used as fallback
 */
const DefaultLoading = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

/**
 * Creates a lazy-loaded component with a loading fallback.
 * This helps reduce the initial bundle size by code-splitting.
 *
 * @param importFunc - A function that returns a dynamic import
 * @param options - Configuration options
 * @returns A lazy-loaded component
 *
 * @example
 * const LazyComponent = lazyLoad(() => import('../components/HeavyComponent'));
 *
 * // Then use it like a regular component
 * <LazyComponent prop1="value" />
 */
export function lazyLoad<T extends React.ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
) {
  const {
    minDelay = 0,
    fallback = <DefaultLoading />
  } = options;

  // If there's a minimum delay, add it to the import promise
  const importWithDelay = minDelay > 0
    ? () => Promise.all([
        importFunc(),
        new Promise(resolve => setTimeout(resolve, minDelay))
      ]).then(([module]) => module)
    : importFunc;

  // Create the lazy component
  const LazyComponent = lazy(importWithDelay);

  // Return a component that wraps the lazy component with Suspense
  return (props: React.ComponentProps<T>) => (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
}

export default lazyLoad;
