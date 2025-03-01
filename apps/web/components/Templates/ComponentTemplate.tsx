import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { cn } from '@/lib/utils';

// Define component props with TypeScript
interface ComponentTemplateProps {
  /** Primary title for the component */
  title: string;
  /** Optional description text */
  description?: string;
  /** Optional CSS class names to apply to the component */
  className?: string;
  /** Optional children elements */
  children?: React.ReactNode;
  /** Optional callback function when the component is clicked */
  onClick?: () => void;
  /** Optional flag to indicate if the component is in a loading state */
  isLoading?: boolean;
  /** Optional flag to indicate if the component is disabled */
  disabled?: boolean;
}

/**
 * ComponentTemplate - A reusable component template following project standards
 *
 * This component serves as a template for creating new components in the project.
 * It includes common patterns like state management, responsive design, and proper TypeScript typing.
 *
 * @example
 * ```tsx
 * <ComponentTemplate
 *   title="My Component"
 *   description="This is a description"
 *   onClick={() => console.log('Clicked!')}
 * >
 *   <p>Child content goes here</p>
 * </ComponentTemplate>
 * ```
 */
export const ComponentTemplate: React.FC<ComponentTemplateProps> = ({
  title,
  description,
  className,
  children,
  onClick,
  isLoading = false,
  disabled = false,
}) => {
  // Example of component state
  const [isActive, setIsActive] = useState<boolean>(false);

  // Example of router usage
  const router = useRouter();

  // Example of useEffect for component lifecycle
  useEffect(() => {
    // Component mount logic
    const handleResize = () => {
      // Example window resize handler
      console.log('Window resized');
    };

    window.addEventListener('resize', handleResize);

    // Component cleanup logic
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Example of event handler
  const handleClick = () => {
    if (disabled || isLoading) return;

    setIsActive(!isActive);

    if (onClick) {
      onClick();
    }
  };

  return (
    <div
      className={cn(
        // Base styles
        'rounded-lg border p-4 shadow-sm transition-all',
        // Conditional styles
        isActive ? 'border-primary bg-primary/5' : 'border-border bg-background',
        isLoading && 'opacity-70 cursor-wait',
        disabled && 'opacity-50 cursor-not-allowed',
        // Custom styles passed as props
        className
      )}
      onClick={handleClick}
      aria-disabled={disabled || isLoading}
      role="region"
      aria-label={title}
    >
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-foreground">{title}</h3>

        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-4">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <div className="mt-4">{children}</div>
        )}
      </div>
    </div>
  );
};

export default ComponentTemplate;
