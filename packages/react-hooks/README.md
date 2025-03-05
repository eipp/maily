# @maily/react-hooks

A collection of React hooks for use in Maily applications.

## Installation

```bash
npm install @maily/react-hooks
# or
yarn add @maily/react-hooks
```

## Available Hooks

### Authentication

#### `useAuth`

A hook that provides authentication state and methods.

```jsx
import { useAuth, AuthProvider } from '@maily/react-hooks';

// Wrap your app with the AuthProvider
function App() {
  return (
    <AuthProvider>
      <YourApp />
    </AuthProvider>
  );
}

// Use the hook in your components
function Profile() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  
  if (!isAuthenticated) {
    return (
      <button onClick={() => login('user@example.com', 'password')}>
        Log in
      </button>
    );
  }
  
  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <button onClick={logout}>Log out</button>
    </div>
  );
}
```

### Feature Flags

#### `useFeatureFlag`

A hook that checks if a specific feature flag is enabled.

```jsx
import { useFeatureFlag } from '@maily/react-hooks';

function NewFeature() {
  const isEnabled = useFeatureFlag('new-feature');
  
  if (!isEnabled) {
    return null;
  }
  
  return <div>New Feature UI</div>;
}
```

With options:

```jsx
const isEnabled = useFeatureFlag('new-feature', {
  apiEndpoint: '/custom/api/feature-flags',
  defaultValue: true // Use this value while loading
});
```

#### `useFeatureFlags`

A hook that fetches and checks multiple feature flags.

```jsx
import { useFeatureFlags } from '@maily/react-hooks';

function FeatureFlaggedUI() {
  const { features, isLoading, error, refresh } = useFeatureFlags([
    'new-editor',
    'advanced-analytics',
    'beta-features'
  ]);
  
  if (isLoading) return <div>Loading features...</div>;
  
  if (error) return <div>Error loading features</div>;
  
  return (
    <div>
      {features['new-editor'] && <NewEditor />}
      {features['advanced-analytics'] && <AdvancedAnalytics />}
      {features['beta-features'] && <BetaFeatures />}
      
      <button onClick={refresh}>Refresh feature flags</button>
    </div>
  );
}
```

#### `isFeatureEnabled`

A utility function to check if a feature is enabled without using React hooks.

```jsx
import { isFeatureEnabled } from '@maily/react-hooks';

// Check if a feature is enabled for a specific user
const enabled = isFeatureEnabled('feature-name', { 
  user: { id: 'user-123', role: 'admin' } 
});
```

## Feature Flag Structure

Feature flags have the following structure:

```js
{
  name: 'feature-name',
  enabled: false, // globally enabled/disabled
  enabledForUsers: ['user-id-1', 'user-id-2'], // enabled for specific users
  enabledForRoles: ['admin', 'beta-tester'], // enabled for specific roles
  config: { // optional configuration for the feature
    maxItems: 10,
    theme: 'dark'
  }
}
```

## API Endpoints

The hooks expect the following API endpoints:

- `GET /api/feature-flags/:featureName` - Get a specific feature flag
- `GET /api/feature-flags?names=flag1&names=flag2` - Get multiple feature flags

## License

MIT 