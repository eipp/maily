import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { dynamicImport } from '../../utils/dynamicImports';

interface TestComponentProps extends Record<string, unknown> {
  message: string;
}

describe('dynamicImport', () => {
  const TestComponent: React.FC<TestComponentProps> = ({ message }) => <div>{message}</div>;

  it('should load a component dynamically', async () => {
    const DynamicComponent = dynamicImport<TestComponentProps>(() =>
      Promise.resolve({ default: TestComponent })
    );
    render(<DynamicComponent message="test" />);
    expect(await screen.findByText('test')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    const neverResolve = new Promise<{ default: React.ComponentType<TestComponentProps> }>(
      () => {}
    );
    const DynamicComponent = dynamicImport<TestComponentProps>(() => neverResolve);
    render(<DynamicComponent message="test" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should handle errors', async () => {
    const error = new Error('Failed to load');
    const DynamicComponent = dynamicImport<TestComponentProps>(() =>
      Promise.reject<{ default: React.ComponentType<TestComponentProps> }>(error)
    );
    render(<DynamicComponent message="test" />);
    expect(
      await screen.findByText(`Error loading component: ${error.message}`)
    ).toBeInTheDocument();
  });
});
