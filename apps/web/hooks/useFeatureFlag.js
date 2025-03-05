import { useState, useEffect, useContext, createContext } from 'react';
import axios from 'axios';

// Create a context for feature flags
const FeatureFlagsContext = createContext({
  features: {},
  loading: true,
  error: null,
  refreshFeatures: () => {},
});

/**
 * Provider component that fetches and provides feature flags to the app
 */
export function FeatureFlagsProvider({ children }) {
  const [features, setFeatures] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFeatures = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/features');
      setFeatures(response.data.features || {});
      setError(null);
    } catch (err) {
      console.error('Failed to fetch feature flags:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch features on initial load
  useEffect(() => {
    fetchFeatures();
  }, []);

  // Value to be provided to consumers
  const value = {
    features,
    loading,
    error,
    refreshFeatures: fetchFeatures,
  };

  return (
    <FeatureFlagsContext.Provider value={value}>
      {children}
    </FeatureFlagsContext.Provider>
  );
}

/**
 * Hook for checking if a specific feature flag is enabled
 * 
 * @param {string} featureName - Name of the feature to check
 * @returns {object} - Object containing the feature's enabled status and loading state
 * 
 * @example
 * const { enabled, loading } = useFeatureFlag('new-campaign-editor');
 * 
 * if (loading) return <Loading />;
 * 
 * return (
 *   <>
 *     {enabled ? <NewCampaignEditor /> : <LegacyCampaignEditor />}
 *   </>
 * );
 */
export function useFeatureFlag(featureName) {
  const { features, loading, error } = useContext(FeatureFlagsContext);

  // Check if the feature exists in our loaded features
  const featureData = features[featureName];
  const enabled = featureData?.enabled || false;

  return {
    enabled,
    loading,
    error,
    description: featureData?.description || '',
  };
}

/**
 * Hook for accessing all feature flags
 * 
 * @returns {object} - Object containing all feature flags and their loading state
 * 
 * @example
 * const { features, loading, refreshFeatures } = useFeatureFlags();
 * 
 * if (loading) return <Loading />;
 * 
 * return (
 *   <FeatureFlagList features={features} onRefresh={refreshFeatures} />
 * );
 */
export function useFeatureFlags() {
  return useContext(FeatureFlagsContext);
}

/**
 * Higher-order component that conditionally renders based on feature flag
 * 
 * @param {string} featureName - Name of the feature to check
 * @param {React.Component} Component - Component to render if feature is enabled
 * @param {React.Component} FallbackComponent - Component to render if feature is disabled
 * @returns {React.Component} - Wrapped component that renders based on feature flag
 * 
 * @example
 * const NewFeature = withFeatureFlag('new-feature', NewComponent, OldComponent);
 */
export function withFeatureFlag(featureName, Component, FallbackComponent) {
  return function FeatureFlaggedComponent(props) {
    const { enabled, loading } = useFeatureFlag(featureName);

    if (loading) {
      // You could return a loading component here
      return null;
    }

    return enabled ? <Component {...props} /> : FallbackComponent ? <FallbackComponent {...props} /> : null;
  };
}

export default useFeatureFlag; 