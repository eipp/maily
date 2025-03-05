import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth';

/**
 * Feature flag configuration
 * @typedef {Object} FeatureFlag
 * @property {string} name - The name of the feature flag
 * @property {boolean} enabled - Whether the feature is enabled globally
 * @property {string[]} [enabledForUsers] - List of user IDs for which the feature is enabled
 * @property {string[]} [enabledForRoles] - List of roles for which the feature is enabled
 * @property {Object} [config] - Additional configuration for the feature
 */

/**
 * In-memory cache for feature flags
 * @type {Object.<string, FeatureFlag>}
 */
const featureFlagsCache = {};

/**
 * Default API endpoint for feature flags
 */
const DEFAULT_API_ENDPOINT = '/api/feature-flags';

/**
 * Check if a feature is enabled for the current user
 * @param {string} featureName - The name of the feature to check
 * @param {Object} [options] - Options for checking the feature
 * @param {Object} [options.user] - User object to check against (defaults to authenticated user)
 * @param {string} [options.apiEndpoint] - Custom API endpoint for feature flags
 * @returns {boolean} - Whether the feature is enabled
 */
export const isFeatureEnabled = (featureName, options = {}) => {
  const featureFlag = featureFlagsCache[featureName];
  
  if (!featureFlag) {
    return false;
  }

  // If the feature is globally enabled, return true
  if (featureFlag.enabled) {
    return true;
  }

  const user = options.user || {};
  
  // Check if enabled for specific user
  if (featureFlag.enabledForUsers && user.id) {
    if (featureFlag.enabledForUsers.includes(user.id)) {
      return true;
    }
  }
  
  // Check if enabled for user's role
  if (featureFlag.enabledForRoles && user.role) {
    if (featureFlag.enabledForRoles.includes(user.role)) {
      return true;
    }
  }
  
  return false;
};

/**
 * Hook to check if a specific feature flag is enabled
 * @param {string} featureName - The name of the feature to check
 * @param {Object} [options] - Options for the feature flag
 * @param {string} [options.apiEndpoint] - Custom API endpoint for feature flags
 * @param {boolean} [options.defaultValue=false] - Default value if the feature flag is not found
 * @returns {boolean} - Whether the feature is enabled
 */
export function useFeatureFlag(featureName, options = {}) {
  const { apiEndpoint = DEFAULT_API_ENDPOINT, defaultValue = false } = options;
  const [isEnabled, setIsEnabled] = useState(defaultValue);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user, isAuthenticated } = useAuth();

  const fetchFeatureFlag = useCallback(async () => {
    if (!featureName) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Check if we already have this feature flag in cache
      if (featureFlagsCache[featureName]) {
        const enabled = isFeatureEnabled(featureName, { user });
        setIsEnabled(enabled);
        setIsLoading(false);
        return;
      }

      // Fetch the feature flag from the API
      const response = await fetch(`${apiEndpoint}/${featureName}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch feature flag: ${response.statusText}`);
      }
      
      const featureFlag = await response.json();
      
      // Cache the feature flag
      featureFlagsCache[featureName] = featureFlag;
      
      // Check if the feature is enabled for the current user
      const enabled = isFeatureEnabled(featureName, { user });
      setIsEnabled(enabled);
    } catch (err) {
      console.error('Error fetching feature flag:', err);
      setError(err);
      setIsEnabled(defaultValue);
    } finally {
      setIsLoading(false);
    }
  }, [featureName, apiEndpoint, defaultValue, user]);

  useEffect(() => {
    fetchFeatureFlag();
  }, [fetchFeatureFlag, isAuthenticated]);

  return isEnabled;
}

/**
 * Hook to fetch and check multiple feature flags
 * @param {string[]} featureNames - Array of feature names to check
 * @param {Object} [options] - Options for the feature flags
 * @param {string} [options.apiEndpoint] - Custom API endpoint for feature flags
 * @returns {Object} - Object containing the status of each feature flag
 */
export function useFeatureFlags(featureNames = [], options = {}) {
  const { apiEndpoint = DEFAULT_API_ENDPOINT } = options;
  const [features, setFeatures] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user, isAuthenticated } = useAuth();

  const fetchFeatureFlags = useCallback(async () => {
    if (!featureNames.length) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Check which feature flags we need to fetch
      const flagsToFetch = featureNames.filter(name => !featureFlagsCache[name]);
      
      if (flagsToFetch.length > 0) {
        // Fetch the feature flags from the API
        const queryParams = new URLSearchParams();
        flagsToFetch.forEach(name => queryParams.append('names', name));
        
        const response = await fetch(`${apiEndpoint}?${queryParams.toString()}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch feature flags: ${response.statusText}`);
        }
        
        const fetchedFlags = await response.json();
        
        // Cache the fetched feature flags
        fetchedFlags.forEach(flag => {
          featureFlagsCache[flag.name] = flag;
        });
      }
      
      // Check if each feature is enabled for the current user
      const featureStatuses = {};
      featureNames.forEach(name => {
        featureStatuses[name] = isFeatureEnabled(name, { user });
      });
      
      setFeatures(featureStatuses);
    } catch (err) {
      console.error('Error fetching feature flags:', err);
      setError(err);
      
      // Set all features to false if there's an error
      const featureStatuses = {};
      featureNames.forEach(name => {
        featureStatuses[name] = false;
      });
      
      setFeatures(featureStatuses);
    } finally {
      setIsLoading(false);
    }
  }, [featureNames, apiEndpoint, user]);

  useEffect(() => {
    fetchFeatureFlags();
  }, [fetchFeatureFlags, isAuthenticated]);

  return {
    features,
    isLoading,
    error,
    refresh: fetchFeatureFlags
  };
}

// Default export
export default useFeatureFlag; 