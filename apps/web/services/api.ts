/**
 * API Service for Maily
 *
 * This service provides methods for interacting with the Maily API,
 * including platform integrations using Nango.
 */

import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Platform Integration API

/**
 * Get authorization URL for connecting a platform
 * @param platform Platform ID to connect
 * @returns Authorization URL and connection details
 */
export const getNangoAuthURL = async (platform: string) => {
  const response = await api.post('/integrations/connect', { platform });
  return response.data;
};

/**
 * Get list of connected platforms
 * @returns List of connected platforms with sync status
 */
export const getConnectedPlatforms = async () => {
  const response = await api.get('/integrations/connections');
  return response.data;
};

/**
 * Trigger synchronization for a platform and sync type
 * @param platform Platform ID to sync
 * @param syncType Type of data to sync (e.g., 'contacts', 'messages')
 * @returns Sync result
 */
export const triggerNangoSync = async (platform: string, syncType: string) => {
  const response = await api.post('/integrations/sync', { platform, sync_type: syncType });
  return response.data;
};

/**
 * Disconnect a platform
 * @param platform Platform ID to disconnect
 * @returns Disconnection result
 */
export const disconnectPlatform = async (platform: string) => {
  const response = await api.delete(`/integrations/${platform}`);
  return response.data;
};

/**
 * Get synchronized data for a platform and sync type
 * @param platform Platform ID to get data for
 * @param syncType Type of data to get (e.g., 'contacts', 'messages')
 * @param limit Maximum number of records to return
 * @param cursor Pagination cursor
 * @returns Synchronized data
 */
export const getPlatformData = async (
  platform: string,
  syncType: string,
  limit: number = 100,
  cursor?: string
) => {
  const params = { limit, ...(cursor ? { cursor } : {}) };
  const response = await api.get(`/integrations/${platform}/${syncType}/data`, { params });
  return response.data;
};

// Campaign API

/**
 * Create a new campaign
 * @param campaignData Campaign data
 * @returns Campaign creation result
 */
export const createCampaign = async (campaignData: any) => {
  const response = await api.post('/campaigns', campaignData);
  return response.data;
};

/**
 * Get campaign details
 * @param campaignId Campaign ID
 * @returns Campaign details
 */
export const getCampaign = async (campaignId: string) => {
  const response = await api.get(`/campaigns/${campaignId}`);
  return response.data;
};

/**
 * Update campaign
 * @param campaignId Campaign ID
 * @param campaignData Campaign data to update
 * @returns Updated campaign
 */
export const updateCampaign = async (campaignId: string, campaignData: any) => {
  const response = await api.put(`/campaigns/${campaignId}`, campaignData);
  return response.data;
};

/**
 * Delete campaign
 * @param campaignId Campaign ID
 * @returns Deletion result
 */
export const deleteCampaign = async (campaignId: string) => {
  const response = await api.delete(`/campaigns/${campaignId}`);
  return response.data;
};

// User API

/**
 * Get current user profile
 * @returns User profile
 */
export const getUserProfile = async () => {
  const response = await api.get('/users/me');
  return response.data;
};

/**
 * Update user profile
 * @param profileData Profile data to update
 * @returns Updated profile
 */
export const updateUserProfile = async (profileData: any) => {
  const response = await api.put('/users/me', profileData);
  return response.data;
};

// Authentication API

/**
 * Login user
 * @param email User email
 * @param password User password
 * @returns Authentication result with token
 */
export const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login', { email, password });
  if (response.data.token) {
    localStorage.setItem('auth_token', response.data.token);
  }
  return response.data;
};

/**
 * Register new user
 * @param userData User registration data
 * @returns Registration result
 */
export const register = async (userData: any) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};

/**
 * Logout user
 */
export const logout = () => {
  localStorage.removeItem('auth_token');
};

export default api;
