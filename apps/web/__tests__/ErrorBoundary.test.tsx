import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ErrorBoundary } from 'packages/error-handling/src/react/ErrorBoundary';

// Component that throws an error for testing
const ThrowError = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Prevent console.error from cluttering test output
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    const { getByText } = render(
      <ErrorBoundary>
        <div>Normal content</div>
      </ErrorBoundary>
    );

    expect(getByText('Normal content')).toBeInTheDocument();
  });

  it('renders error UI when there is an error', () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong.')).toBeInTheDocument();
    expect(screen.getByText('Error Details')).toBeInTheDocument();
    expect(onError).toHaveBeenCalled();
  });

  it('allows recovery via try again button', () => {
    const TestComponent = ({ shouldThrow = true }) => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>Normal content</div>;
    };
    
    const { rerender } = render(
      <ErrorBoundary>
        <TestComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    const tryAgainButton = screen.getByText('Try again');
    
    // Mock component to no longer throw
    rerender(
      <ErrorBoundary>
        <TestComponent shouldThrow={false} />
      </ErrorBoundary>
    );
    
    fireEvent.click(tryAgainButton);
    
    // After reset, normal content should be visible
    expect(screen.getByText('Normal content')).toBeInTheDocument();
  });
});