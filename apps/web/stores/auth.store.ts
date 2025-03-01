/**
 * Authentication state management using Zustand
 *
 * This store handles user authentication state across the application,
 * providing a consistent interface for login, logout, and session management.
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { type User } from 'apps/web/types/user';

// Define the auth state interface
interface AuthState {
  // State
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  lastLogin: Date | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  loginWithToken: (token: string) => Promise<void>;
  loginWithSso: (provider: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;

  // Helpers
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string | string[]) => boolean;
}

/**
 * Auth store using Zustand with persistence, immer, and devtools
 *
 * Features:
 * - Persistent login state across page refreshes
 * - Immutable state updates via immer
 * - Dev tools integration for debugging
 * - Type-safe actions and state
 */
export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      immer(
        (set, get) => ({
          // Initial state
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
          lastLogin: null,

          /**
           * Log in with email and password
           */
          login: async (email, password) => {
            try {
              set(state => {
                state.isLoading = true;
                state.error = null;
              });

              const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
              });

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Authentication failed');
              }

              const data = await response.json();

              set(state => {
                state.user = data.user;
                state.token = data.token;
                state.isAuthenticated = true;
                state.isLoading = false;
                state.lastLogin = new Date();
              });

              // Store token in secure HttpOnly cookie from the API response
              // The token itself is also stored in the state for API calls
            } catch (error: any) {
              set(state => {
                state.error = error.message;
                state.isLoading = false;
                state.isAuthenticated = false;
                state.user = null;
                state.token = null;
              });

              throw error; // Re-throw for the component to handle
            }
          },

          /**
           * Log in with an existing token
           */
          loginWithToken: async (token) => {
            try {
              set(state => {
                state.isLoading = true;
                state.error = null;
              });

              const response = await fetch('/api/auth/me', {
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                }
              });

              if (!response.ok) {
                throw new Error('Invalid or expired token');
              }

              const user = await response.json();

              set(state => {
                state.user = user;
                state.token = token;
                state.isAuthenticated = true;
                state.isLoading = false;
                state.lastLogin = new Date();
              });
            } catch (error: any) {
              set(state => {
                state.error = error.message;
                state.isLoading = false;
                state.isAuthenticated = false;
                state.user = null;
                state.token = null;
              });

              // Silent failure for token login attempts
              // The UI should fall back to the login form
            }
          },

          /**
           * Log in with SSO provider (OAuth)
           */
          loginWithSso: async (provider) => {
            try {
              set(state => {
                state.isLoading = true;
                state.error = null;
              });

              // Start the SSO flow - this will redirect to the provider
              // The actual OAuth flow is handled by next-auth
              window.location.href = `/api/auth/signin/${provider}`;

              // This function doesn't resolve since there's a redirect
              // The auth state will be updated when redirected back to the app
              return new Promise<void>(() => {});
            } catch (error: any) {
              set(state => {
                state.error = error.message;
                state.isLoading = false;
              });

              throw error;
            }
          },

          /**
           * Log out the current user
           */
          logout: async () => {
            try {
              set(state => {
                state.isLoading = true;
              });

              // Call logout endpoint to clear server-side session
              await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${get().token}`
                }
              });

              // Clear state regardless of API response
              set(state => {
                state.user = null;
                state.token = null;
                state.isAuthenticated = false;
                state.isLoading = false;
                state.error = null;
              });
            } catch (error) {
              // Still clear auth state even if API call fails
              set(state => {
                state.user = null;
                state.token = null;
                state.isAuthenticated = false;
                state.isLoading = false;
                state.error = null;
              });
            }
          },

          /**
           * Refresh the current user's data
           */
          refreshUser: async () => {
            const token = get().token;
            if (!token) return;

            try {
              set(state => {
                state.isLoading = true;
              });

              const response = await fetch('/api/auth/me', {
                headers: {
                  'Authorization': `Bearer ${token}`
                }
              });

              if (!response.ok) {
                throw new Error('Failed to refresh user data');
              }

              const user = await response.json();

              set(state => {
                state.user = user;
                state.isLoading = false;
              });
            } catch (error: any) {
              set(state => {
                state.isLoading = false;
                // Don't set error or clear auth state on refresh failures
              });
            }
          },

          /**
           * Clear any authentication errors
           */
          clearError: () => {
            set(state => {
              state.error = null;
            });
          },

          /**
           * Check if the user has a specific permission
           */
          hasPermission: (permission) => {
            const { user } = get();
            if (!user) return false;

            return user.permissions?.includes(permission) || false;
          },

          /**
           * Check if the user has at least one of the specified roles
           */
          hasRole: (role) => {
            const { user } = get();
            if (!user?.role) return false;

            const roles = Array.isArray(role) ? role : [role];
            return roles.includes(user.role);
          }
        })
      ),
      {
        name: 'auth-storage',
        storage: createJSONStorage(() => sessionStorage), // Use sessionStorage for better security
        partialize: (state) => ({
          // Only persist these fields, omit sensitive data and loading states
          token: state.token,
          user: {
            id: state.user?.id,
            email: state.user?.email,
            name: state.user?.name,
            role: state.user?.role,
            permissions: state.user?.permissions,
            // Omit other potentially sensitive user data
          },
          isAuthenticated: state.isAuthenticated,
          lastLogin: state.lastLogin,
        }),
      }
    ),
    {
      name: 'auth-store',
      enabled: process.env.NODE_ENV !== 'production',
    }
  )
);

// Export auth selectors for use in components
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectCurrentUser = (state: AuthState) => state.user;
export const selectAuthError = (state: AuthState) => state.error;
export const selectAuthIsLoading = (state: AuthState) => state.isLoading;
