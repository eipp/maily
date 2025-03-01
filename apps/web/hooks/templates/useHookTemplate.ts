import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Hook template interface for input parameters
 */
interface UseHookTemplateOptions<T> {
  /** Initial data value */
  initialData?: T;
  /** Optional fetch function to get data */
  fetchFn?: () => Promise<T>;
  /** Whether to fetch data on mount */
  fetchOnMount?: boolean;
  /** Optional callback when data changes */
  onDataChange?: (data: T) => void;
  /** Optional error handler */
  onError?: (error: Error) => void;
}

/**
 * Hook template interface for return values
 */
interface UseHookTemplateReturn<T> {
  /** Current data value */
  data: T | undefined;
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: Error | null;
  /** Function to manually fetch data */
  fetchData: () => Promise<void>;
  /** Function to update data */
  setData: (newData: T) => void;
  /** Function to reset to initial state */
  reset: () => void;
}

/**
 * useHookTemplate - A reusable hook template following project standards
 *
 * This hook serves as a template for creating new custom hooks in the project.
 * It includes common patterns like data fetching, loading states, and error handling.
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, fetchData } = useHookTemplate<User[]>({
 *   fetchFn: async () => await api.getUsers(),
 *   fetchOnMount: true,
 *   onError: (err) => console.error('Failed to fetch users:', err)
 * });
 * ```
 */
export function useHookTemplate<T>(options: UseHookTemplateOptions<T> = {}): UseHookTemplateReturn<T> {
  // Destructure options with defaults
  const {
    initialData,
    fetchFn,
    fetchOnMount = true,
    onDataChange,
    onError,
  } = options;

  // State management
  const [data, setData] = useState<T | undefined>(initialData);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  // Use a ref to track if the component is mounted
  const isMounted = useRef<boolean>(false);

  // Fetch data function wrapped in useCallback to prevent unnecessary re-renders
  const fetchData = useCallback(async (): Promise<void> => {
    // Skip if no fetch function provided
    if (!fetchFn) return;

    try {
      setIsLoading(true);
      setError(null);

      const result = await fetchFn();

      // Only update state if component is still mounted
      if (isMounted.current) {
        setData(result);

        // Call onDataChange callback if provided
        if (onDataChange) {
          onDataChange(result);
        }
      }
    } catch (err) {
      // Only update state if component is still mounted
      if (isMounted.current) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);

        // Call onError callback if provided
        if (onError) {
          onError(error);
        }
      }
    } finally {
      // Only update state if component is still mounted
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [fetchFn, onDataChange, onError]);

  // Update data function
  const updateData = useCallback((newData: T): void => {
    setData(newData);

    // Call onDataChange callback if provided
    if (onDataChange) {
      onDataChange(newData);
    }
  }, [onDataChange]);

  // Reset function
  const reset = useCallback((): void => {
    setData(initialData);
    setIsLoading(false);
    setError(null);
  }, [initialData]);

  // Effect to fetch data on mount if fetchOnMount is true
  useEffect(() => {
    isMounted.current = true;

    if (fetchOnMount && fetchFn) {
      fetchData();
    }

    // Cleanup function to set isMounted to false when component unmounts
    return () => {
      isMounted.current = false;
    };
  }, [fetchOnMount, fetchFn, fetchData]);

  return {
    data,
    isLoading,
    error,
    fetchData,
    setData: updateData,
    reset,
  };
}

export default useHookTemplate;
