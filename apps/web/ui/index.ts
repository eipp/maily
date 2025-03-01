/**
 * UI Components for Maily
 *
 * This file exports UI components used throughout the application.
 * These are placeholder interfaces for TypeScript compatibility.
 */

// Button Component
export interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
  color?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}

export const Button = (props: ButtonProps) => null;

// Card Component
export interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export const Card = (props: CardProps) => null;

// Icon Component
export interface IconProps {
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  color?: string;
}

export const Icon = (props: IconProps) => null;

// Spinner Component
export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  className?: string;
}

export const Spinner = (props: SpinnerProps) => null;

// Alert Component
export interface AlertProps {
  children: React.ReactNode;
  type?: 'info' | 'success' | 'warning' | 'error';
  className?: string;
  onClose?: () => void;
}

export const Alert = (props: AlertProps) => null;

// Badge Component
export interface BadgeProps {
  children: React.ReactNode;
  color?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'gray' | 'red' | 'green' | 'yellow';
  variant?: 'solid' | 'outline';
  className?: string;
  title?: string;
}

export const Badge = (props: BadgeProps) => null;
