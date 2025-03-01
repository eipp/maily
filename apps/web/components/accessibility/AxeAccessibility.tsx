import React, { useEffect, ReactNode } from 'react';

export interface AxeAccessibilityProps {
  children: ReactNode;
  options?: {
    rules?: Record<string, { enabled: boolean }>;
    disableForms?: boolean;
    disableFrame?: boolean;
    disableHidden?: boolean;
    disableUncaughtPromiseRejection?: boolean;
  };
}

/**
 * A component that injects axe-core accessibility testing in development mode
 * This helps developers identify accessibility issues during development
 */
const AxeAccessibility: React.FC<AxeAccessibilityProps> = ({
  children,
  options = {}
}) => {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      // Only load axe-core in development mode
      const loadAxe = async () => {
        const axe = await import('@axe-core/react');
        const React = await import('react');
        const ReactDOM = await import('react-dom');

        // Initialize axe with custom options
        axe.default(React.default, ReactDOM.default, 1000, options);

        // Log a message to the console
        console.log(
          '%cAccessibility testing is active. Check the console for results.',
          'background: #4CAF50; color: white; padding: 4px; border-radius: 4px;'
        );
      };

      loadAxe().catch(err => {
        console.error('Error loading axe-core:', err);
      });
    }
  }, [options]);

  return <>{children}</>;
};

export default AxeAccessibility;
