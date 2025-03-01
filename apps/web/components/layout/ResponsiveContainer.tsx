import React from 'react';

interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  as?: React.ElementType;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full' | 'none';
  padding?: boolean;
}

/**
 * A responsive container component that adapts to different screen sizes.
 * This component ensures consistent layout across different devices.
 */
const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className = '',
  as: Component = 'div',
  maxWidth = 'xl',
  padding = true,
}) => {
  // Max width classes
  const maxWidthClasses = {
    xs: 'max-w-xs',
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-full',
    none: '',
  };

  // Padding classes - responsive padding that adjusts based on screen size
  const paddingClasses = padding
    ? 'px-4 sm:px-6 md:px-8'
    : '';

  // Combine all classes
  const containerClasses = `
    w-full mx-auto
    ${maxWidthClasses[maxWidth]}
    ${paddingClasses}
    ${className}
  `.trim();

  return (
    <Component className={containerClasses}>
      {children}
    </Component>
  );
};

export default ResponsiveContainer;
