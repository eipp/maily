/**
 * feature-flags.js
 * Configuration system for feature flags across different environments.
 * 
 * Usage:
 *   import { isFeatureEnabled } from '../config/feature-flags';
 *   
 *   if (isFeatureEnabled('new-campaign-editor')) {
 *     // Show new editor
 *   } else {
 *     // Show old editor
 *   }
 */

// Import environment configuration
const { getCurrentEnvironment, ENVIRONMENTS } = require('./environments');

// Feature definitions with environment-specific controls
const featureFlags = {
  // New Campaign Editor - enabled in all environments except production
  'new-campaign-editor': {
    description: 'New drag-and-drop campaign editor with enhanced analytics',
    enabledIn: [ENVIRONMENTS.DEVELOPMENT, ENVIRONMENTS.TESTING, ENVIRONMENTS.STAGING],
    rolloutPercentage: {
      [ENVIRONMENTS.DEVELOPMENT]: 100,
      [ENVIRONMENTS.TESTING]: 100,
      [ENVIRONMENTS.STAGING]: 100,
      [ENVIRONMENTS.PRODUCTION]: 0
    }
  },
  
  // AI-powered content suggestions - beta feature
  'ai-content-suggestions': {
    description: 'AI-powered content suggestions for email campaigns',
    enabledIn: [ENVIRONMENTS.DEVELOPMENT, ENVIRONMENTS.TESTING],
    rolloutPercentage: {
      [ENVIRONMENTS.DEVELOPMENT]: 100,
      [ENVIRONMENTS.TESTING]: 50,
      [ENVIRONMENTS.STAGING]: 0,
      [ENVIRONMENTS.PRODUCTION]: 0
    }
  },
  
  // Advanced Analytics Dashboard
  'advanced-analytics': {
    description: 'Enhanced analytics dashboard with cohort analysis',
    enabledIn: [ENVIRONMENTS.DEVELOPMENT, ENVIRONMENTS.TESTING, ENVIRONMENTS.STAGING, ENVIRONMENTS.PRODUCTION],
    rolloutPercentage: {
      [ENVIRONMENTS.DEVELOPMENT]: 100,
      [ENVIRONMENTS.TESTING]: 100,
      [ENVIRONMENTS.STAGING]: 100,
      [ENVIRONMENTS.PRODUCTION]: 20 // Gradual rollout in production
    }
  },
  
  // Multi-language Support
  'multi-language': {
    description: 'Support for multiple languages in the UI',
    enabledIn: [ENVIRONMENTS.DEVELOPMENT, ENVIRONMENTS.TESTING],
    rolloutPercentage: {
      [ENVIRONMENTS.DEVELOPMENT]: 100,
      [ENVIRONMENTS.TESTING]: 100,
      [ENVIRONMENTS.STAGING]: 0,
      [ENVIRONMENTS.PRODUCTION]: 0
    }
  },
  
  // Team Collaboration Features
  'team-collaboration': {
    description: 'Enhanced team collaboration tools',
    enabledIn: [ENVIRONMENTS.DEVELOPMENT, ENVIRONMENTS.TESTING, ENVIRONMENTS.STAGING],
    rolloutPercentage: {
      [ENVIRONMENTS.DEVELOPMENT]: 100,
      [ENVIRONMENTS.TESTING]: 100,
      [ENVIRONMENTS.STAGING]: 50,
      [ENVIRONMENTS.PRODUCTION]: 0
    }
  }
};

// Get current environment using centralized function
const getEnvironment = () => {
  // First check for environment variable
  return getCurrentEnvironment();
};

// Generate a consistent hash for a user ID to ensure the same users
// consistently get the same experience
const hashUserID = (userID) => {
  let hash = 0;
  
  if (!userID || userID.length === 0) {
    return hash;
  }
  
  for (let i = 0; i < userID.length; i++) {
    const char = userID.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  
  // Normalize to a percentage (0-100)
  return Math.abs(hash) % 100;
};

/**
 * Check if a feature is enabled for the current environment
 * 
 * @param {string} featureName - Name of the feature to check
 * @param {object} options - Additional options
 * @param {string} options.userID - User ID for percentage rollout
 * @param {string} options.environment - Override environment detection
 * @returns {boolean} - Whether the feature is enabled
 */
const isFeatureEnabled = (featureName, options = {}) => {
  // Get feature configuration
  const feature = featureFlags[featureName];
  
  // If feature doesn't exist, it's disabled
  if (!feature) {
    return false;
  }
  
  // Get current environment or use override
  const environment = options.environment || getEnvironment();
  
  // Check if feature is enabled in this environment
  if (!feature.enabledIn.includes(environment)) {
    return false;
  }
  
  // If no percentage rollout is defined, feature is fully enabled
  if (!feature.rolloutPercentage || feature.rolloutPercentage[environment] === undefined) {
    return true;
  }
  
  // If rollout percentage is 0, feature is disabled
  if (feature.rolloutPercentage[environment] === 0) {
    return false;
  }
  
  // If rollout percentage is 100, feature is fully enabled
  if (feature.rolloutPercentage[environment] === 100) {
    return true;
  }
  
  // For percentage rollout, we need a user ID
  const userID = options.userID;
  if (!userID) {
    // Without user ID, default to disabled for partial rollouts
    return false;
  }
  
  // Check if user is in the rollout percentage
  const userPercentile = hashUserID(userID);
  return userPercentile < feature.rolloutPercentage[environment];
};

/**
 * Get all feature flags with their status for the current environment
 * 
 * @param {object} options - Additional options
 * @param {string} options.userID - User ID for percentage rollout
 * @param {string} options.environment - Override environment detection
 * @returns {object} - Object with feature names as keys and enabled status as values
 */
const getAllFeatures = (options = {}) => {
  const result = {};
  
  Object.keys(featureFlags).forEach(featureName => {
    result[featureName] = {
      enabled: isFeatureEnabled(featureName, options),
      description: featureFlags[featureName].description
    };
  });
  
  return result;
};

module.exports = {
  isFeatureEnabled,
  getAllFeatures,
  _getEnvironment: getEnvironment, // Exported for testing
  _featureFlags: featureFlags // Exported for testing
}; 