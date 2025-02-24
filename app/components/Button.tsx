import React, { ButtonHTMLAttributes } from 'react';
import classNames from 'classnames';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'lg';
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size,
  className,
  ...props
}) => {
  const buttonClasses = classNames(
    'inline-flex items-center justify-center rounded-md font-medium transition-colors',
    {
      'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
      'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
      'px-3 py-1.5 text-sm': size === 'sm',
      'px-6 py-3 text-lg': size === 'lg',
      'px-4 py-2 text-base': !size,
    },
    `btn-${variant}`,
    size && `btn-${size}`,
    className
  );

  return (
    <button
      className={buttonClasses}
      type="button"
      {...props}
    >
      {children}
    </button>
  );
}; 