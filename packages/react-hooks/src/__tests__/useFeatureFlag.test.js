import { renderHook, act } from '@testing-library/react-hooks';
import { useFeatureFlag, useFeatureFlags, isFeatureEnabled } from '../useFeatureFlag';
import { useAuth } from '../useAuth';

// Mock the useAuth hook
jest.mock('../useAuth', () => ({
  useAuth: jest.fn()
}));

// Mock fetch
global.fetch = jest.fn();

describe('useFeatureFlag', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock useAuth to return a default user
    useAuth.mockReturnValue({
      user: { id: 'user-123', role: 'user' },
      isAuthenticated: true
    });
    
    // Mock fetch to return a successful response
    global.fetch.mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        name: 'test-feature',
        enabled: false,
        enabledForUsers: ['user-123'],
        enabledForRoles: ['admin']
      })
    });
  });
  
  it('should return the default value while loading', async () => {
    const { result } = renderHook(() => useFeatureFlag('test-feature', { defaultValue: true }));
    
    // Initially it should return the default value
    expect(result.current).toBe(true);
    
    // Wait for the hook to finish loading
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    // After loading, it should return the actual value
    expect(result.current).toBe(true); // Enabled for user-123
  });
  
  it('should fetch the feature flag from the API', async () => {
    renderHook(() => useFeatureFlag('test-feature'));
    
    expect(global.fetch).toHaveBeenCalledWith('/api/feature-flags/test-feature');
  });
  
  it('should use a custom API endpoint if provided', async () => {
    renderHook(() => useFeatureFlag('test-feature', { apiEndpoint: '/custom/api' }));
    
    expect(global.fetch).toHaveBeenCalledWith('/custom/api/test-feature');
  });
  
  it('should return true if the feature is enabled globally', async () => {
    // Mock fetch to return a globally enabled feature
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({
        name: 'test-feature',
        enabled: true
      })
    });
    
    const { result, waitForNextUpdate } = renderHook(() => useFeatureFlag('test-feature'));
    
    await waitForNextUpdate();
    
    expect(result.current).toBe(true);
  });
  
  it('should return true if the feature is enabled for the user', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useFeatureFlag('test-feature'));
    
    await waitForNextUpdate();
    
    expect(result.current).toBe(true);
  });
  
  it('should return true if the feature is enabled for the user role', async () => {
    // Mock useAuth to return a user with admin role
    useAuth.mockReturnValue({
      user: { id: 'other-user', role: 'admin' },
      isAuthenticated: true
    });
    
    const { result, waitForNextUpdate } = renderHook(() => useFeatureFlag('test-feature'));
    
    await waitForNextUpdate();
    
    expect(result.current).toBe(true);
  });
  
  it('should return false if the feature is not enabled for the user', async () => {
    // Mock useAuth to return a different user
    useAuth.mockReturnValue({
      user: { id: 'other-user', role: 'user' },
      isAuthenticated: true
    });
    
    const { result, waitForNextUpdate } = renderHook(() => useFeatureFlag('test-feature'));
    
    await waitForNextUpdate();
    
    expect(result.current).toBe(false);
  });
  
  it('should handle API errors gracefully', async () => {
    // Mock fetch to return an error
    global.fetch.mockRejectedValueOnce(new Error('API error'));
    
    const { result, waitForNextUpdate } = renderHook(() => useFeatureFlag('test-feature', { defaultValue: true }));
    
    await waitForNextUpdate();
    
    // Should fall back to the default value
    expect(result.current).toBe(true);
  });
});

describe('useFeatureFlags', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock useAuth to return a default user
    useAuth.mockReturnValue({
      user: { id: 'user-123', role: 'user' },
      isAuthenticated: true
    });
    
    // Mock fetch to return a successful response
    global.fetch.mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue([
        {
          name: 'feature-1',
          enabled: true
        },
        {
          name: 'feature-2',
          enabled: false,
          enabledForUsers: ['user-123']
        },
        {
          name: 'feature-3',
          enabled: false
        }
      ])
    });
  });
  
  it('should fetch multiple feature flags', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useFeatureFlags(['feature-1', 'feature-2', 'feature-3'])
    );
    
    // Initially it should be loading
    expect(result.current.isLoading).toBe(true);
    
    await waitForNextUpdate();
    
    // After loading, it should have the features
    expect(result.current.features).toEqual({
      'feature-1': true,
      'feature-2': true,
      'feature-3': false
    });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
  });
  
  it('should handle API errors gracefully', async () => {
    // Mock fetch to return an error
    global.fetch.mockRejectedValueOnce(new Error('API error'));
    
    const { result, waitForNextUpdate } = renderHook(() => 
      useFeatureFlags(['feature-1', 'feature-2'])
    );
    
    await waitForNextUpdate();
    
    // Should set all features to false
    expect(result.current.features).toEqual({
      'feature-1': false,
      'feature-2': false
    });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).not.toBe(null);
  });
  
  it('should refresh feature flags when called', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useFeatureFlags(['feature-1'])
    );
    
    await waitForNextUpdate();
    
    // Reset the fetch mock
    global.fetch.mockClear();
    
    // Call refresh
    await act(async () => {
      await result.current.refresh();
    });
    
    // Should fetch the feature flags again
    expect(global.fetch).toHaveBeenCalled();
  });
});

describe('isFeatureEnabled', () => {
  beforeEach(() => {
    // Reset the feature flags cache
    global.featureFlagsCache = {};
  });
  
  it('should return false if the feature flag is not found', () => {
    expect(isFeatureEnabled('non-existent-feature')).toBe(false);
  });
  
  it('should return true if the feature is globally enabled', () => {
    // Set up the cache
    global.featureFlagsCache = {
      'test-feature': {
        name: 'test-feature',
        enabled: true
      }
    };
    
    expect(isFeatureEnabled('test-feature')).toBe(true);
  });
  
  it('should return true if the feature is enabled for the user', () => {
    // Set up the cache
    global.featureFlagsCache = {
      'test-feature': {
        name: 'test-feature',
        enabled: false,
        enabledForUsers: ['user-123']
      }
    };
    
    expect(isFeatureEnabled('test-feature', { user: { id: 'user-123' } })).toBe(true);
    expect(isFeatureEnabled('test-feature', { user: { id: 'other-user' } })).toBe(false);
  });
  
  it('should return true if the feature is enabled for the user role', () => {
    // Set up the cache
    global.featureFlagsCache = {
      'test-feature': {
        name: 'test-feature',
        enabled: false,
        enabledForRoles: ['admin']
      }
    };
    
    expect(isFeatureEnabled('test-feature', { user: { role: 'admin' } })).toBe(true);
    expect(isFeatureEnabled('test-feature', { user: { role: 'user' } })).toBe(false);
  });
}); 