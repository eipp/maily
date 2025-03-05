import React from 'react';
import { useFeatureFlag, useFeatureFlags, AuthProvider } from '../src';

// Example component that uses a single feature flag
function NewFeature() {
  const isEnabled = useFeatureFlag('new-feature');
  
  if (!isEnabled) {
    return <p>This feature is not available yet.</p>;
  }
  
  return (
    <div className="new-feature">
      <h2>New Feature</h2>
      <p>This is a new feature that is only visible when the feature flag is enabled.</p>
    </div>
  );
}

// Example component that uses multiple feature flags
function FeatureFlaggedUI() {
  const { features, isLoading, error, refresh } = useFeatureFlags([
    'new-editor',
    'advanced-analytics',
    'beta-features'
  ]);
  
  if (isLoading) {
    return <div>Loading features...</div>;
  }
  
  if (error) {
    return (
      <div className="error">
        <p>Error loading features: {error.message}</p>
        <button onClick={refresh}>Try Again</button>
      </div>
    );
  }
  
  return (
    <div className="feature-flagged-ui">
      <h2>Feature Flagged UI</h2>
      
      {features['new-editor'] && (
        <div className="feature">
          <h3>New Editor</h3>
          <p>This is the new editor experience.</p>
        </div>
      )}
      
      {features['advanced-analytics'] && (
        <div className="feature">
          <h3>Advanced Analytics</h3>
          <p>These are the advanced analytics features.</p>
        </div>
      )}
      
      {features['beta-features'] && (
        <div className="feature">
          <h3>Beta Features</h3>
          <p>These features are still in beta.</p>
        </div>
      )}
      
      <button onClick={refresh}>Refresh Features</button>
    </div>
  );
}

// Example component with conditional rendering based on feature flags
function ConditionalFeature() {
  const isNewUiEnabled = useFeatureFlag('new-ui');
  const isExperimentalEnabled = useFeatureFlag('experimental-features');
  
  return (
    <div className="conditional-feature">
      <h2>Conditional Feature</h2>
      
      {isNewUiEnabled ? (
        <div className="new-ui">
          <p>This is the new UI experience.</p>
          {isExperimentalEnabled && (
            <div className="experimental">
              <p>This is an experimental feature within the new UI.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="classic-ui">
          <p>This is the classic UI experience.</p>
        </div>
      )}
    </div>
  );
}

// Main example component
export default function FeatureFlagExample() {
  return (
    <AuthProvider>
      <div className="feature-flag-example">
        <h1>Feature Flag Examples</h1>
        
        <section>
          <h2>Single Feature Flag</h2>
          <NewFeature />
        </section>
        
        <section>
          <h2>Multiple Feature Flags</h2>
          <FeatureFlaggedUI />
        </section>
        
        <section>
          <h2>Conditional Rendering</h2>
          <ConditionalFeature />
        </section>
      </div>
    </AuthProvider>
  );
} 