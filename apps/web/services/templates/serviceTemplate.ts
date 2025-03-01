/**
 * Service Template
 *
 * This module serves as a template for creating service modules
 * that handle API communication and data processing.
 */

import { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { apiClient } from '@/lib/api';

/**
 * Error response interface
 */
export interface ErrorResponse {
  status: string;
  message: string;
  code: number;
  details?: string;
}

/**
 * Base response interface
 */
export interface BaseResponse<T> {
  data: T;
  status: number;
  message: string;
  timestamp: string;
}

/**
 * Pagination parameters interface
 */
export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * Resource item interface
 */
export interface ResourceItem {
  id: string;
  [key: string]: any;
}

/**
 * Service template class
 */
export class ServiceTemplate<T extends ResourceItem> {
  /**
   * Base API endpoint path
   */
  private basePath: string;

  /**
   * Constructor
   *
   * @param resourcePath - The API resource path
   */
  constructor(resourcePath: string) {
    this.basePath = `/api/v1/${resourcePath}`;
  }

  /**
   * Get all resources with optional pagination
   *
   * @param params - Optional pagination parameters
   * @returns Promise with the response data
   *
   * @example
   * ```ts
   * const { data } = await userService.getAll({ page: 1, limit: 10 });
   * ```
   */
  async getAll(params?: PaginationParams): Promise<BaseResponse<T[]>> {
    try {
      const response: AxiosResponse<BaseResponse<T[]>> = await apiClient.get(
        this.basePath,
        { params }
      );
      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ErrorResponse>);
    }
  }

  /**
   * Get a resource by ID
   *
   * @param id - Resource ID
   * @returns Promise with the response data
   *
   * @example
   * ```ts
   * const { data } = await userService.getById('user-123');
   * ```
   */
  async getById(id: string): Promise<BaseResponse<T>> {
    try {
      const response: AxiosResponse<BaseResponse<T>> = await apiClient.get(
        `${this.basePath}/${id}`
      );
      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ErrorResponse>);
    }
  }

  /**
   * Create a new resource
   *
   * @param data - Resource data
   * @returns Promise with the response data
   *
   * @example
   * ```ts
   * const { data } = await userService.create({ name: 'John Doe', email: 'john@example.com' });
   * ```
   */
  async create(data: Partial<T>): Promise<BaseResponse<T>> {
    try {
      const response: AxiosResponse<BaseResponse<T>> = await apiClient.post(
        this.basePath,
        data
      );
      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ErrorResponse>);
    }
  }

  /**
   * Update a resource
   *
   * @param id - Resource ID
   * @param data - Resource data to update
   * @returns Promise with the response data
   *
   * @example
   * ```ts
   * const { data } = await userService.update('user-123', { name: 'Updated Name' });
   * ```
   */
  async update(id: string, data: Partial<T>): Promise<BaseResponse<T>> {
    try {
      const response: AxiosResponse<BaseResponse<T>> = await apiClient.put(
        `${this.basePath}/${id}`,
        data
      );
      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ErrorResponse>);
    }
  }

  /**
   * Delete a resource
   *
   * @param id - Resource ID
   * @returns Promise with the response data
   *
   * @example
   * ```ts
   * const { data } = await userService.delete('user-123');
   * ```
   */
  async delete(id: string): Promise<BaseResponse<boolean>> {
    try {
      const response: AxiosResponse<BaseResponse<boolean>> = await apiClient.delete(
        `${this.basePath}/${id}`
      );
      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ErrorResponse>);
    }
  }

  /**
   * Custom API request
   *
   * @param config - Axios request configuration
   * @returns Promise with the response data
   *
   * @example
   * ```ts
   * const { data } = await userService.request({
   *   method: 'post',
   *   url: '/api/v1/users/validate',
   *   data: { email: 'test@example.com' }
   * });
   * ```
   */
  async request<R = any>(config: AxiosRequestConfig): Promise<BaseResponse<R>> {
    try {
      const response: AxiosResponse<BaseResponse<R>> = await apiClient.request(config);
      return response.data;
    } catch (error) {
      return this.handleError(error as AxiosError<ErrorResponse>);
    }
  }

  /**
   * Handle API errors
   *
   * @param error - Axios error
   * @throws Error with formatted message
   */
  private handleError<R>(error: AxiosError<ErrorResponse>): never {
    const status = error.response?.status || 500;
    const message = error.response?.data?.message || error.message || 'Unknown error';
    const details = error.response?.data?.details;

    // Log error for debugging
    console.error(`API Error (${status}):`, message, details || '');

    // Throw formatted error
    throw new Error(`API Error (${status}): ${message}${details ? ` - ${details}` : ''}`);
  }
}

/**
 * Create a service instance for a specific resource
 *
 * @param resourcePath - The API resource path
 * @returns Service instance
 *
 * @example
 * ```ts
 * interface User extends ResourceItem {
 *   name: string;
 *   email: string;
 * }
 *
 * const userService = createService<User>('users');
 * ```
 */
export function createService<T extends ResourceItem>(resourcePath: string): ServiceTemplate<T> {
  return new ServiceTemplate<T>(resourcePath);
}

export default ServiceTemplate;
