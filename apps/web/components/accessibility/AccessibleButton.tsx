import React, { useRef } from 'react';
import { useButton } from '@react-aria/button';

interface AccessibleButtonProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  onPress?: () => void;
  isDisabled?: boolean;
  autoFocus?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

/**
 * An accessible button component built with React Aria
 * This component ensures proper keyboard navigation, focus management,
 * and screen reader support.
 */
const AccessibleButton: React.FC<AccessibleButtonProps> = ({
  children,
  className = '',
  variant = 'primary',
  size = 'md',
  ...props
}) => {
  const ref = useRef<HTMLButtonElement>(null);
  const { buttonProps } = useButton(props, ref);

  // Base classes for all buttons
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors';

  // Size-specific classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  // Variant-specific classes
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 active:bg-gray-400',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 active:bg-gray-100',
    ghost: 'text-gray-700 hover:bg-gray-100 active:bg-gray-200',
  };

  const classes = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`;

  return (
    <button
      {...buttonProps}
      ref={ref}
      className={classes}
      data-variant={variant}
      data-size={size}
    >
      {children}
    </button>
  );
};

export default AccessibleButton;
