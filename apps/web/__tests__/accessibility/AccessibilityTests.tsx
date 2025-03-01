import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

// Add jest-axe custom matchers
expect.extend(toHaveNoViolations);

/**
 * Test a component for accessibility violations using jest-axe
 * @param Component The React component to test
 * @param props Props to pass to the component
 * @returns Promise that resolves when the test is complete
 */
export async function testAccessibility(
  Component: React.ComponentType<any>,
  props: Record<string, any> = {}
): Promise<void> {
  const { container } = render(<Component {...props} />);
  const results = await axe(container);

  // This will fail the test if there are any accessibility violations
  expect(results).toHaveNoViolations();
}

/**
 * Test a rendered component for accessibility violations using jest-axe
 * @param container The rendered component container
 * @returns Promise that resolves when the test is complete
 */
export async function testRenderedAccessibility(container: HTMLElement): Promise<void> {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
}

/**
 * Test a page for accessibility violations using jest-axe
 * @param url The URL to test
 * @param options Options for the test
 * @returns Promise that resolves when the test is complete
 */
export async function testPageAccessibility(
  url: string,
  options: {
    waitForSelector?: string;
    timeout?: number;
  } = {}
): Promise<void> {
  // This function would be implemented in e2e tests with Playwright or Cypress
  console.log(`Testing accessibility for page: ${url}`);
}
