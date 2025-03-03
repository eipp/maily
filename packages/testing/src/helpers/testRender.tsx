import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

/**
 * Custom render options extending React Testing Library's RenderOptions
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  /**
   * Initial route path
   */
  route?: string;
  
  /**
   * Initial state for context providers
   */
  state?: {
    auth?: {
      isAuthenticated?: boolean;
      user?: {
        id: string;
        email: string;
        name?: string;
      } | null;
    };
    theme?: 'light' | 'dark';
    [key: string]: any;
  };
  
  /**
   * Additional context providers to wrap the component with
   */
  providers?: React.ComponentType<{ children: ReactNode }>[];
}

/**
 * Test providers wrapper component for rendering
 */
const TestProviders: React.FC<{
  children: ReactNode;
  state?: CustomRenderOptions['state'];
  providers?: React.ComponentType<{ children: ReactNode }>[];
}> = ({ children, state, providers = [] }) => {
  const defaultState = {
    auth: {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        name: 'Test User',
      },
    },
    theme: 'light',
    ...state,
  };

  // Mock context providers would go here
  const MockAuthProvider = ({ children }: { children: ReactNode }) => (
    <div data-testid="mock-auth-provider" data-state={JSON.stringify(defaultState.auth)}>
      {children}
    </div>
  );

  const MockThemeProvider = ({ children }: { children: ReactNode }) => (
    <div data-testid="mock-theme-provider" data-theme={defaultState.theme}>
      {children}
    </div>
  );

  // Add default providers
  const allProviders = [MockAuthProvider, MockThemeProvider, ...providers];

  // Wrap the component with all providers
  return allProviders.reduce(
    (acc, Provider) => <Provider>{acc}</Provider>,
    <>{children}</>
  );
};

/**
 * Custom render function that wraps components with test providers
 * 
 * @param ui - The component to render
 * @param options - Custom render options
 * @returns The render result plus user-event instance
 */
function customRender(
  ui: ReactElement,
  options: CustomRenderOptions = {}
) {
  const {
    route,
    state,
    providers,
    ...renderOptions
  } = options;

  // Mock route navigation if needed
  if (route) {
    // Would implement route setting here
  }

  const user = userEvent.setup();

  const returnValue = {
    ...render(ui, {
      wrapper: ({ children }) => (
        <TestProviders state={state} providers={providers}>
          {children}
        </TestProviders>
      ),
      ...renderOptions,
    }),
    user,
  };

  return returnValue;
}

// Re-export everything from React Testing Library
export * from '@testing-library/react';

// Override render method
export { customRender as render };