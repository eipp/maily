import { ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines multiple class values into a single className string
 * using clsx and tailwind-merge to handle conditional classes
 * and properly merge Tailwind CSS classes.
 *
 * @param inputs - Class values to be combined
 * @returns A string of combined class names
 * 
 * @example
 * // Basic usage
 * cn('text-red-500', 'bg-blue-500')
 * // => 'text-red-500 bg-blue-500'
 * 
 * @example
 * // With conditionals
 * cn('text-white', { 'bg-blue-500': true, 'bg-red-500': false })
 * // => 'text-white bg-blue-500'
 * 
 * @example
 * // With Tailwind merge
 * cn('px-2 py-1', 'py-2')
 * // => 'px-2 py-2'
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}