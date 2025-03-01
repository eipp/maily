import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundaryWrapper } from '../components/ErrorBoundary';

// Component that throws an error for testing
const ThrowError = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Prevent console.error from cluttering test output
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    const { getByText } = render(
      <ErrorBoundaryWrapper>
        <div>Normal content</div>
      </ErrorBoundaryWrapper>
    );

    expect(getByText('Normal content')).toBeInTheDocument();
  });

  it('renders error UI when there is an error', () => {
    const onError = jest.fn();

    render(
      <ErrorBoundaryWrapper onError={onError}>
        <ThrowError />
      </ErrorBoundaryWrapper>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
    expect(onError).toHaveBeenCalled();
  });

  it('allows recovery via try again button', () => {
    const onReset = jest.fn();

    render(
      <ErrorBoundaryWrapper onReset={onReset}>
        <ThrowError />
      </ErrorBoundaryWrapper>
    );

    const tryAgainButton = screen.getByText('Try again');
    fireEvent.click(tryAgainButton);

    expect(onReset).toHaveBeenCalled();
  });
});
