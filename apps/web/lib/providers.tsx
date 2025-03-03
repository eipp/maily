import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ThemeProvider } from 'next-themes';
import { SWRConfig } from 'swr';
import config from './config';

// User context
type User = {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
} | null;

type UserContextType = {
  user: User;
  setUser: (user: User) => void;
  isLoading: boolean;
  isAuthenticated: boolean;
};

const UserContext = createContext<UserContextType>({
  user: null,
  setUser: () => {},
  isLoading: true,
  isAuthenticated: false,
});

// Feature flags context
type FeatureFlagsContextType = {
  aiMesh: boolean;
  trustVerification: boolean;
  realTimeCollaboration: boolean;
};

const FeatureFlagsContext = createContext<FeatureFlagsContextType>({
  aiMesh: false,
  trustVerification: false,
  realTimeCollaboration: false,
});

// UI context
type UIContextType = {
  isSidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  isAnalyticsPanelOpen: boolean;
  setAnalyticsPanelOpen: (open: boolean) => void;
  isReasoningPanelOpen: boolean;
  setReasoningPanelOpen: (open: boolean) => void;
};

const UIContext = createContext<UIContextType>({
  isSidebarOpen: true,
  setSidebarOpen: () => {},
  isAnalyticsPanelOpen: false,
  setAnalyticsPanelOpen: () => {},
  isReasoningPanelOpen: false,
  setReasoningPanelOpen: () => {},
});

// Mode context
export type OperationalMode = 'content' | 'campaign' | 'analytics' | 'audience';

type ModeContextType = {
  mode: OperationalMode;
  setMode: (mode: OperationalMode) => void;
};

const ModeContext = createContext<ModeContextType>({
  mode: 'content',
  setMode: () => {},
});

// Combined provider component
type ProvidersProps = {
  children: ReactNode;
};

export function Providers({ children }: ProvidersProps) {
  // User state
  const [user, setUser] = useState<User>(null);
  const [isLoading, setIsLoading] = useState(true);

  // UI state
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [isAnalyticsPanelOpen, setAnalyticsPanelOpen] = useState(false);
  const [isReasoningPanelOpen, setReasoningPanelOpen] = useState(false);

  // Mode state
  const [mode, setMode] = useState<OperationalMode>('content');

  // Feature flags
  const featureFlags = {
    aiMesh: config.features.aiMesh,
    trustVerification: config.features.trustVerification,
    realTimeCollaboration: config.features.realTimeCollaboration,
  };

  // SWR configuration
  const swrConfig = {
    fetcher: (url: string) => fetch(url).then((res) => res.json()),
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  };

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch(`${config.urls.api}/api/auth/session`);
        if (response.ok) {
          const data = await response.json();
          if (data.user) {
            setUser(data.user);
          }
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <SWRConfig value={swrConfig}>
        <UserContext.Provider
          value={{
            user,
            setUser,
            isLoading,
            isAuthenticated: !!user,
          }}
        >
          <FeatureFlagsContext.Provider value={featureFlags}>
            <UIContext.Provider
              value={{
                isSidebarOpen,
                setSidebarOpen,
                isAnalyticsPanelOpen,
                setAnalyticsPanelOpen,
                isReasoningPanelOpen,
                setReasoningPanelOpen,
              }}
            >
              <ModeContext.Provider value={{ mode, setMode }}>
                {children}
              </ModeContext.Provider>
            </UIContext.Provider>
          </FeatureFlagsContext.Provider>
        </UserContext.Provider>
      </SWRConfig>
    </ThemeProvider>
  );
}

// Custom hooks for accessing context
export const useUser = () => useContext(UserContext);
export const useFeatureFlags = () => useContext(FeatureFlagsContext);
export const useUI = () => useContext(UIContext);
export const useMode = () => useContext(ModeContext);
