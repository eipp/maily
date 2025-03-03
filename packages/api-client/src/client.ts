import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import axiosRetry from 'axios-retry';
import { ApiError } from './errors/ApiError';
import { NetworkError } from './errors/NetworkError';

export interface MailyApiClientConfig {
  /**
   * Base URL for the API
   */
  baseUrl: string;
  
  /**
   * API key for authentication
   */
  apiKey?: string;
  
  /**
   * Authentication token (alternative to apiKey)
   */
  token?: string;
  
  /**
   * Request timeout in milliseconds
   */
  timeout?: number;
  
  /**
   * Retry configuration
   */
  retry?: {
    /**
     * Number of retries
     */
    retries: number;
    
    /**
     * Whether to retry on network errors
     */
    retryOnNetworkError: boolean;
    
    /**
     * HTTP status codes to retry on
     */
    statusCodesToRetry: number[];
    
    /**
     * Retry delay in milliseconds
     */
    retryDelay: number;
  };
}

/**
 * Maily API client for interacting with the Maily API
 */
export class MailyApiClient {
  private axiosInstance: AxiosInstance;
  private config: MailyApiClientConfig;
  
  /**
   * Create a new MailyApiClient instance
   * 
   * @param config - API client configuration
   */
  constructor(config: MailyApiClientConfig) {
    this.config = config;
    
    // Create axios instance
    this.axiosInstance = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(config.apiKey ? { 'X-API-Key': config.apiKey } : {}),
        ...(config.token ? { 'Authorization': `Bearer ${config.token}` } : {}),
      },
    });
    
    // Configure retry behavior
    if (config.retry) {
      axiosRetry(this.axiosInstance, {
        retries: config.retry.retries,
        retryDelay: (retryCount) => {
          return config.retry?.retryDelay 
            ? config.retry.retryDelay * retryCount 
            : axiosRetry.exponentialDelay(retryCount);
        },
        retryCondition: (error) => {
          // Retry on network errors if configured
          if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
            return !!config.retry?.retryOnNetworkError;
          }
          
          // Retry on specific status codes
          if (error.response) {
            return config.retry?.statusCodesToRetry.includes(error.response.status) || false;
          }
          
          return false;
        },
      });
    }
    
    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // The request was made and the server responded with an error status
          throw new ApiError(
            error.response.data.message || 'API error',
            error.response.status,
            error.response.data
          );
        } else if (error.request) {
          // The request was made but no response was received
          throw new NetworkError('Network error - no response received', error.request);
        } else {
          // Something happened in setting up the request
          throw new Error(`Error setting up request: ${error.message}`);
        }
      }
    );
  }
  
  /**
   * Make a GET request to the API
   * 
   * @param url - API endpoint URL
   * @param config - Axios request configuration
   * @returns Promise resolving to the response data
   */
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.get(url, config);
    return response.data;
  }
  
  /**
   * Make a POST request to the API
   * 
   * @param url - API endpoint URL
   * @param data - Request payload
   * @param config - Axios request configuration
   * @returns Promise resolving to the response data
   */
  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.post(url, data, config);
    return response.data;
  }
  
  /**
   * Make a PUT request to the API
   * 
   * @param url - API endpoint URL
   * @param data - Request payload
   * @param config - Axios request configuration
   * @returns Promise resolving to the response data
   */
  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.put(url, data, config);
    return response.data;
  }
  
  /**
   * Make a PATCH request to the API
   * 
   * @param url - API endpoint URL
   * @param data - Request payload
   * @param config - Axios request configuration
   * @returns Promise resolving to the response data
   */
  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.patch(url, data, config);
    return response.data;
  }
  
  /**
   * Make a DELETE request to the API
   * 
   * @param url - API endpoint URL
   * @param config - Axios request configuration
   * @returns Promise resolving to the response data
   */
  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.delete(url, config);
    return response.data;
  }
  
  /**
   * Set the authentication token for the API client
   * 
   * @param token - Authentication token
   */
  public setToken(token: string): void {
    this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }
  
  /**
   * Set the API key for the API client
   * 
   * @param apiKey - API key
   */
  public setApiKey(apiKey: string): void {
    this.axiosInstance.defaults.headers.common['X-API-Key'] = apiKey;
  }
  
  /**
   * Create a new instance of the API client with the given configuration
   * 
   * @param config - API client configuration
   * @returns New API client instance
   */
  public static create(config: MailyApiClientConfig): MailyApiClient {
    return new MailyApiClient(config);
  }
}