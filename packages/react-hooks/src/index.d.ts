// Authentication types
export interface User {
  id: string;
  name?: string;
  email?: string;
  role?: string;
  [key: string]: any;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: Error | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
}

export interface AuthProviderProps {
  children: React.ReactNode;
}

// Feature flag types
export interface FeatureFlag {
  name: string;
  enabled: boolean;
  enabledForUsers?: string[];
  enabledForRoles?: string[];
  config?: Record<string, any>;
}

export interface FeatureFlagOptions {
  apiEndpoint?: string;
  defaultValue?: boolean;
}

export interface FeatureFlagsResult {
  features: Record<string, boolean>;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export interface IsFeatureEnabledOptions {
  user?: User;
  apiEndpoint?: string;
}

// Authentication hooks
export function useAuth(): AuthContextType;
export function AuthProvider(props: AuthProviderProps): JSX.Element;

// Feature flag hooks
export function useFeatureFlag(featureName: string, options?: FeatureFlagOptions): boolean;
export function useFeatureFlags(featureNames: string[], options?: FeatureFlagOptions): FeatureFlagsResult;
export function isFeatureEnabled(featureName: string, options?: IsFeatureEnabledOptions): boolean;

// Default export
export default useFeatureFlag; 