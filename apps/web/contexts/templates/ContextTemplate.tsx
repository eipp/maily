import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

/**
 * Context state interface
 */
interface ContextState {
  /** Example data property */
  data: any[];
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: Error | null;
}

/**
 * Context actions interface
 */
interface ContextActions {
  /** Function to fetch data */
  fetchData: () => Promise<void>;
  /** Function to add an item */
  addItem: (item: any) => void;
  /** Function to update an item */
  updateItem: (id: string, updates: any) => void;
  /** Function to remove an item */
  removeItem: (id: string) => void;
  /** Function to clear all data */
  clearData: () => void;
}

/**
 * Combined context value interface
 */
interface ContextValue extends ContextState, ContextActions {}

/**
 * Context provider props interface
 */
interface ContextProviderProps {
  /** Initial data to populate the context */
  initialData?: any[];
  /** Children components */
  children: ReactNode;
}

/**
 * Default context state
 */
const defaultContextState: ContextState = {
  data: [],
  isLoading: false,
  error: null,
};

/**
 * Create the context with a default undefined value
 */
const ContextTemplate = createContext<ContextValue | undefined>(undefined);

/**
 * Context provider component
 *
 * @example
 * ```tsx
 * <ContextProvider initialData={[...]}>
 *   <YourComponent />
 * </ContextProvider>
 * ```
 */
export const ContextProvider: React.FC<ContextProviderProps> = ({
  initialData = [],
  children,
}) => {
  // State management
  const [state, setState] = useState<ContextState>({
    ...defaultContextState,
    data: initialData,
  });

  // Example API fetch function
  const fetchData = useCallback(async (): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      // Mock API call - replace with actual API call
      const response = await new Promise<any[]>(resolve => {
        setTimeout(() => {
          resolve([
            { id: '1', name: 'Item 1' },
            { id: '2', name: 'Item 2' },
          ]);
        }, 1000);
      });

      setState(prev => ({
        ...prev,
        data: response,
        isLoading: false,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error : new Error(String(error)),
      }));
    }
  }, []);

  // Add item function
  const addItem = useCallback((item: any): void => {
    setState(prev => ({
      ...prev,
      data: [...prev.data, item],
    }));
  }, []);

  // Update item function
  const updateItem = useCallback((id: string, updates: any): void => {
    setState(prev => ({
      ...prev,
      data: prev.data.map(item =>
        item.id === id ? { ...item, ...updates } : item
      ),
    }));
  }, []);

  // Remove item function
  const removeItem = useCallback((id: string): void => {
    setState(prev => ({
      ...prev,
      data: prev.data.filter(item => item.id !== id),
    }));
  }, []);

  // Clear data function
  const clearData = useCallback((): void => {
    setState(prev => ({
      ...prev,
      data: [],
    }));
  }, []);

  // Effect for initialization
  useEffect(() => {
    // Optional: Fetch data on mount
    // fetchData();

    return () => {
      // Cleanup if needed
    };
  }, []);

  // Combine state and actions for context value
  const value: ContextValue = {
    ...state,
    fetchData,
    addItem,
    updateItem,
    removeItem,
    clearData,
  };

  return (
    <ContextTemplate.Provider value={value}>
      {children}
    </ContextTemplate.Provider>
  );
};

/**
 * Custom hook to use the context
 *
 * @throws Error if used outside of a ContextProvider
 * @returns Context value with state and actions
 *
 * @example
 * ```tsx
 * const { data, isLoading, fetchData, addItem } = useContextTemplate();
 * ```
 */
export const useContextTemplate = (): ContextValue => {
  const context = useContext(ContextTemplate);

  if (context === undefined) {
    throw new Error('useContextTemplate must be used within a ContextProvider');
  }

  return context;
};

export default ContextTemplate;
