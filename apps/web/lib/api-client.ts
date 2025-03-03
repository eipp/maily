/**
 * API Client for interacting with the JustMaily API
 */
import { getSession } from 'next-auth/react';
import config from './config';

// Types
export type ApiResponse<T> = {
  data: T;
  error?: never;
};

export type ApiError = {
  message: string;
  status: number;
  data?: any;
};

export type ApiResult<T> = ApiResponse<T> | { data?: never; error: ApiError };

// Default request options
const DEFAULT_OPTIONS: RequestInit = {
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Base API client for making HTTP requests to the API
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = config.urls.api) {
    this.baseUrl = baseUrl;
  }

  /**
   * Make a request to the API
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResult<T>> {
    try {
      // Get authentication token from session
      const session = await getSession();
      const token = session?.accessToken;

      // Merge default options with provided options
      const mergedOptions: RequestInit = {
        ...DEFAULT_OPTIONS,
        ...options,
        headers: {
          ...DEFAULT_OPTIONS.headers,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...options.headers,
        },
      };

      // Make the request
      const response = await fetch(`${this.baseUrl}${endpoint}`, mergedOptions);

      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      if (contentType && !contentType.includes('application/json')) {
        if (!response.ok) {
          return {
            error: {
              message: 'Server error',
              status: response.status,
            },
          };
        }
        // For non-JSON successful responses, return empty data object
        return { data: {} as T };
      }

      // Parse JSON response
      const data = await response.json();

      // Handle error responses
      if (!response.ok) {
        return {
          error: {
            message: data.detail || data.message || 'Server error',
            status: response.status,
            data,
          },
        };
      }

      // Return successful response
      return { data: data as T };
    } catch (error) {
      // Handle network errors
      return {
        error: {
          message: error instanceof Error ? error.message : 'Network error',
          status: 0,
        },
      };
    }
  }

  /**
   * Make a GET request to the API
   */
  async get<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * Make a POST request to the API
   */
  async post<T>(
    endpoint: string,
    data: any,
    options: RequestInit = {}
  ): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Make a PUT request to the API
   */
  async put<T>(
    endpoint: string,
    data: any,
    options: RequestInit = {}
  ): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Make a PATCH request to the API
   */
  async patch<T>(
    endpoint: string,
    data: any,
    options: RequestInit = {}
  ): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /**
   * Make a DELETE request to the API
   */
  async delete<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }
}

// Create a singleton instance
export const apiClient = new ApiClient();

export default apiClient;
