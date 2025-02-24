import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { createDynamicComponent } from '../../utils/dynamicImports';
import React from 'react';

// Mock next/dynamic
jest.mock('next/dynamic', () => {
  const mockDynamic = (importFunc: () => Promise<any>, options: any) => {
    const MockComponent = (props: any) => {
      const [Component, setComponent] = React.useState<React.ComponentType | null>(null);
      const [error, setError] = React.useState<Error | null>(null);
      const [isLoading, setIsLoading] = React.useState(true);

      React.useEffect(() => {
        let mounted = true;
        
        const loadComponent = async () => {
          try {
            const module = await importFunc();
            if (mounted) {
              setComponent(() => module.default);
              setIsLoading(false);
            }
          } catch (err) {
            if (mounted) {
              setError(err as Error);
              setIsLoading(false);
            }
          }
        };

        loadComponent();
        
        return () => {
          mounted = false;
        };
      }, []);

      if (error) {
        return options.loading({ error, isLoading: false });
      }

      if (isLoading) {
        return options.loading({ isLoading: true });
      }

      return Component ? <Component {...props} /> : null;
    };

    return MockComponent;
  };

  return mockDynamic;
});

describe('Dynamic Imports', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading component while importing', async () => {
    const TestComponent = () => <div>Test Component</div>;
    const importFunc = () => new Promise<{ default: typeof TestComponent }>(resolve => {
      setTimeout(() => resolve({ default: TestComponent }), 100);
    });

    const DynamicComponent = createDynamicComponent(importFunc);
    render(<DynamicComponent />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders component after successful import', async () => {
    const TestComponent = () => <div>Test Component</div>;
    const importFunc = () => Promise.resolve({ default: TestComponent });

    const DynamicComponent = createDynamicComponent(importFunc);
    render(<DynamicComponent />);

    await waitFor(() => {
      expect(screen.getByText('Test Component')).toBeInTheDocument();
    });
  });

  it('renders error message on import failure', async () => {
    const importFunc = () => Promise.reject(new Error('Failed to load component'));

    const DynamicComponent = createDynamicComponent(importFunc);
    render(<DynamicComponent />);

    await waitFor(() => {
      expect(screen.getByText(/Error loading component:/)).toBeInTheDocument();
    });
  });

  it('renders custom loading component', async () => {
    const TestComponent = () => <div>Test Component</div>;
    const CustomLoading = () => <div>Custom Loading...</div>;
    const importFunc = () => new Promise<{ default: typeof TestComponent }>(resolve => {
      setTimeout(() => resolve({ default: TestComponent }), 100);
    });

    const DynamicComponent = createDynamicComponent(importFunc, {
      loading: CustomLoading
    });
    render(<DynamicComponent />);

    expect(screen.getByText('Custom Loading...')).toBeInTheDocument();
  });

  it('handles timeout', async () => {
    const TestComponent = () => <div>Test Component</div>;
    const importFunc = () => new Promise<{ default: typeof TestComponent }>(resolve => {
      setTimeout(() => resolve({ default: TestComponent }), 1000);
    });

    const DynamicComponent = createDynamicComponent(importFunc, {
      timeout: 500
    });
    render(<DynamicComponent />);

    await waitFor(() => {
      expect(screen.getByText(/Loading timed out/)).toBeInTheDocument();
    }, { timeout: 600 });
  });

  it('respects delay option before showing loading component', async () => {
    const TestComponent = () => <div>Test Component</div>;
    const importFunc = () => new Promise<{ default: typeof TestComponent }>(resolve => {
      setTimeout(() => resolve({ default: TestComponent }), 300);
    });

    const DynamicComponent = createDynamicComponent(importFunc, {
      delay: 200
    });
    render(<DynamicComponent />);

    // Loading should not be visible immediately
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();

    // Loading should be visible after delay
    await waitFor(() => {
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    }, { timeout: 250 });

    // Component should eventually render
    await waitFor(() => {
      expect(screen.getByText('Test Component')).toBeInTheDocument();
    }, { timeout: 350 });
  });

  it('passes props to dynamically imported component', async () => {
    interface TestProps {
      message: string;
    }
    const TestComponent = ({ message }: TestProps) => <div>{message}</div>;
    const importFunc = () => Promise.resolve({ default: TestComponent });

    const DynamicComponent = createDynamicComponent<TestProps>(importFunc);
    render(<DynamicComponent message="Hello World" />);

    await waitFor(() => {
      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });
  });
}); 