import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />);

    // Check if the loading text is rendered
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Check if the spinner element is rendered with the correct classes
    const spinnerElement = document.querySelector('.animate-spin');
    expect(spinnerElement).toBeInTheDocument();
    expect(spinnerElement).toHaveClass('h-8');
    expect(spinnerElement).toHaveClass('w-8');
  });

  it('renders with custom size', () => {
    render(<LoadingSpinner size="lg" />);

    const spinnerElement = document.querySelector('.animate-spin');
    expect(spinnerElement).toHaveClass('h-12');
    expect(spinnerElement).toHaveClass('w-12');
  });

  it('renders with custom label', () => {
    const customLabel = 'Please wait...';
    render(<LoadingSpinner label={customLabel} />);

    expect(screen.getByText(customLabel)).toBeInTheDocument();
  });

  it('renders without label when label is empty', () => {
    render(<LoadingSpinner label="" />);

    const labelElement = screen.queryByText('Loading...');
    expect(labelElement).not.toBeInTheDocument();
  });
});
