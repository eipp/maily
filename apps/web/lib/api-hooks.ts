/**
 * React hooks for interacting with the JustMaily API
 */
import { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useSWR, useSWRConfig } from 'swr';
import apiClient, { ApiResult } from './api-client';

// Types
export type ApiHookState<T> = {
  data: T | null;
  isLoading: boolean;
  isError: boolean;
  error: string | null;
};

export type ApiHookActions<T, P = any> = {
  mutate: (data?: T) => Promise<void>;
  execute: (params?: P) => Promise<ApiResult<T>>;
  reset: () => void;
};

export type ApiHook<T, P = any> = ApiHookState<T> & ApiHookActions<T, P>;

/**
 * Hook for fetching data from the API
 */
export function useApi<T>(endpoint: string, options?: RequestInit): ApiHook<T> {
  const { data: session } = useSession();
  const { mutate } = useSWRConfig();
  const [state, setState] = useState<ApiHookState<T>>({
    data: null,
    isLoading: true,
    isError: false,
    error: null,
  });

  // Fetch data from the API
  const fetchData = useCallback(async (): Promise<ApiResult<T>> => {
    try {
      setState((prev) => ({ ...prev, isLoading: true }));
      const result = await apiClient.get<T>(endpoint, options);

      if (result.error) {
        setState({
          data: null,
          isLoading: false,
          isError: true,
          error: result.error.message,
        });
      } else {
        setState({
          data: result.data,
          isLoading: false,
          isError: false,
          error: null,
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setState({
        data: null,
        isLoading: false,
        isError: true,
        error: errorMessage,
      });
      return { error: { message: errorMessage, status: 0 } };
    }
  }, [endpoint, options]);

  // Execute the fetch manually
  const execute = useCallback(
    async (params?: any): Promise<ApiResult<T>> => {
      if (params) {
        const queryParams = new URLSearchParams(params).toString();
        const url = `${endpoint}${queryParams ? `?${queryParams}` : ''}`;
        return apiClient.get<T>(url, options);
      }
      return fetchData();
    },
    [endpoint, options, fetchData]
  );

  // Mutate the data
  const mutateData = useCallback(
    async (data?: T) => {
      if (data) {
        setState((prev) => ({ ...prev, data }));
      }
      await mutate(endpoint);
    },
    [endpoint, mutate]
  );

  // Reset the state
  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });
  }, []);

  // Fetch data on mount and when session changes
  useEffect(() => {
    fetchData();
  }, [fetchData, session]);

  return {
    ...state,
    mutate: mutateData,
    execute,
    reset,
  };
}

/**
 * Hook for creating data with the API
 */
export function useApiCreate<T, P = any>(endpoint: string): ApiHook<T, P> {
  const [state, setState] = useState<ApiHookState<T>>({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  });

  // Create data with the API
  const execute = useCallback(
    async (params: P): Promise<ApiResult<T>> => {
      try {
        setState((prev) => ({ ...prev, isLoading: true }));
        const result = await apiClient.post<T>(endpoint, params);

        if (result.error) {
          setState({
            data: null,
            isLoading: false,
            isError: true,
            error: result.error.message,
          });
        } else {
          setState({
            data: result.data,
            isLoading: false,
            isError: false,
            error: null,
          });
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setState({
          data: null,
          isLoading: false,
          isError: true,
          error: errorMessage,
        });
        return { error: { message: errorMessage, status: 0 } };
      }
    },
    [endpoint]
  );

  // Mutate the data
  const mutate = useCallback(
    async (data?: T) => {
      if (data) {
        setState((prev) => ({ ...prev, data }));
      }
    },
    []
  );

  // Reset the state
  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    mutate,
    execute,
    reset,
  };
}

/**
 * Hook for updating data with the API
 */
export function useApiUpdate<T, P = any>(endpoint: string): ApiHook<T, P> {
  const [state, setState] = useState<ApiHookState<T>>({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  });

  // Update data with the API
  const execute = useCallback(
    async (params: P): Promise<ApiResult<T>> => {
      try {
        setState((prev) => ({ ...prev, isLoading: true }));
        const result = await apiClient.put<T>(endpoint, params);

        if (result.error) {
          setState({
            data: null,
            isLoading: false,
            isError: true,
            error: result.error.message,
          });
        } else {
          setState({
            data: result.data,
            isLoading: false,
            isError: false,
            error: null,
          });
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setState({
          data: null,
          isLoading: false,
          isError: true,
          error: errorMessage,
        });
        return { error: { message: errorMessage, status: 0 } };
      }
    },
    [endpoint]
  );

  // Mutate the data
  const mutate = useCallback(
    async (data?: T) => {
      if (data) {
        setState((prev) => ({ ...prev, data }));
      }
    },
    []
  );

  // Reset the state
  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    mutate,
    execute,
    reset,
  };
}

/**
 * Hook for deleting data with the API
 */
export function useApiDelete<T>(endpoint: string): ApiHook<T, void> {
  const [state, setState] = useState<ApiHookState<T>>({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  });

  // Delete data with the API
  const execute = useCallback(async (): Promise<ApiResult<T>> => {
    try {
      setState((prev) => ({ ...prev, isLoading: true }));
      const result = await apiClient.delete<T>(endpoint);

      if (result.error) {
        setState({
          data: null,
          isLoading: false,
          isError: true,
          error: result.error.message,
        });
      } else {
        setState({
          data: result.data,
          isLoading: false,
          isError: false,
          error: null,
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setState({
        data: null,
        isLoading: false,
        isError: true,
        error: errorMessage,
      });
      return { error: { message: errorMessage, status: 0 } };
    }
  }, [endpoint]);

  // Mutate the data
  const mutate = useCallback(
    async (data?: T) => {
      if (data) {
        setState((prev) => ({ ...prev, data }));
      }
    },
    []
  );

  // Reset the state
  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    mutate,
    execute,
    reset,
  };
}
