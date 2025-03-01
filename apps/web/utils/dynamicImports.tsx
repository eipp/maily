import React from 'react';
import dynamic from 'next/dynamic';
import type { DynamicOptions } from 'next/dynamic';

interface LoadingProps {
  error?: Error | null;
  isLoading?: boolean;
  pastDelay?: boolean;
  timedOut?: boolean;
}

const DefaultLoading: React.FC<LoadingProps> = ({ error, pastDelay, timedOut }) => {
  if (error) {
    return <div>Error loading component: {error.message}</div>;
  }
  if (timedOut) {
    return <div>Loading timed out</div>;
  }
  if (pastDelay) {
    return <div>Loading...</div>;
  }
  return null;
};

export function createDynamicComponent<P extends Record<string, unknown>>(
  importFunc: () => Promise<{ default: React.ComponentType<P> }>,
  options: Omit<DynamicOptions<P>, 'loader'> = {}
) {
  const defaultOptions: DynamicOptions<P> = {
    loading: (props: { error?: Error | null }) => <DefaultLoading {...props} />,
    ssr: true,
    ...options,
  };

  return dynamic(importFunc, defaultOptions);
}

export function dynamicImport<P extends Record<string, unknown>>(
  importFunc: () => Promise<{ default: React.ComponentType<P> }>,
  options: Omit<DynamicOptions<P>, 'loader'> = {}
) {
  return createDynamicComponent(importFunc, options);
}
