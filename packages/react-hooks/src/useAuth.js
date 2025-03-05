import { useState, useEffect, useContext, createContext } from 'react';

// Create an Auth context
const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  login: () => {},
  logout: () => {},
  register: () => {},
});

/**
 * Auth Provider component that wraps your app and makes auth object available
 * to any child component that calls useAuth().
 */
export function AuthProvider({ children }) {
  const auth = useProvideAuth();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

/**
 * Hook for components to get the auth object and re-render when it changes.
 */
export function useAuth() {
  return useContext(AuthContext);
}

/**
 * Provider hook that creates auth object and handles state
 */
function useProvideAuth() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const isAuthenticated = !!user;
  
  // Handle user state changes
  useEffect(() => {
    // Check for existing session
    const checkAuthState = async () => {
      try {
        setIsLoading(true);
        
        // Call your API to check auth state
        const response = await fetch('/api/auth/session');
        
        if (response.ok) {
          const data = await response.json();
          if (data.user) {
            setUser(data.user);
          } else {
            setUser(null);
          }
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error('Error checking auth state:', err);
        setError(err);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuthState();
    
    // Listen for changes (if using sockets or similar)
    // const unsubscribe = onAuthStateChanged(...)
    
    // Cleanup subscription on unmount
    // return () => unsubscribe();
  }, []);
  
  /**
   * Sign in with email and password
   */
  const login = async (email, password) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Login failed');
      }
      
      const userData = await response.json();
      setUser(userData.user);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  /**
   * Sign out
   */
  const logout = async () => {
    try {
      setIsLoading(true);
      
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      
      setUser(null);
    } catch (err) {
      setError(err.message);
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  /**
   * Register a new user
   */
  const register = async (email, password, name) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email, password, name }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Registration failed');
      }
      
      const userData = await response.json();
      setUser(userData.user);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  // Return the user object and auth methods
  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    register,
  };
}

export default useAuth; 