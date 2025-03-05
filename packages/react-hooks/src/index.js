// Authentication hooks
export { useAuth, AuthProvider } from './useAuth';

// Feature flag hooks
export { 
  useFeatureFlag, 
  useFeatureFlags, 
  isFeatureEnabled 
} from './useFeatureFlag';

// Make useFeatureFlag the default export
export { default } from './useFeatureFlag'; 