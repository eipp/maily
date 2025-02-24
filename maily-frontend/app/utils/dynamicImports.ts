import dynamic from 'next/dynamic';
import { ComponentType, ReactNode } from 'react';

interface LoadingProps {
  error?: Error | null;
  isLoading?: boolean;
  pastDelay?: boolean;
  timedOut?: boolean;
}

interface DynamicImportOptions {
  ssr?: boolean;
  loading?: ComponentType<LoadingProps>;
  delay?: number;
  timeout?: number;
}

const DefaultLoading = ({ error, isLoading, pastDelay, timedOut }: LoadingProps) => {
  if (error) {
    return <div>Error loading component: {error.message}</div>;
  }
  if (timedOut) {
    return <div>Loading timed out. Please try again.</div>;
  }
  if (pastDelay && isLoading) {
    return <div>Loading...</div>;
  }
  return null;
};

export function createDynamicComponent<P extends {}>(
  importFunc: () => Promise<{ default: ComponentType<P> }>,
  options: DynamicImportOptions = {}
) {
  const {
    ssr = false,
    loading = DefaultLoading,
    delay = 200,
    timeout = 10000
  } = options;

  return dynamic(importFunc, {
    loading,
    ssr,
    loadableGenerated: {
      webpack: () => [importFunc.toString()],
      modules: [importFunc.toString()]
    },
    delay,
    timeout
  });
}

// Example usage:
// export const DynamicEditor = createDynamicComponent(
//   () => import('../components/Editor'),
//   {
//     ssr: false,
//     delay: 300,
//     timeout: 5000
//   }
// ); 