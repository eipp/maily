/**
 * Utility template module
 *
 * This module serves as a template for creating utility functions
 * following the project's coding standards.
 */

/**
 * Type definition for formatting options
 */
export interface FormatOptions {
  /** Decimal places for number formatting */
  decimals?: number;
  /** Locale for internationalization */
  locale?: string;
  /** Additional formatting options */
  [key: string]: any;
}

/**
 * Default formatting options
 */
const DEFAULT_FORMAT_OPTIONS: FormatOptions = {
  decimals: 2,
  locale: 'en-US',
};

/**
 * Formats a number according to specified options
 *
 * @param value - The number to format
 * @param options - Formatting options
 * @returns Formatted number as string
 *
 * @example
 * ```ts
 * formatNumber(1234.567); // "1,234.57"
 * formatNumber(1234.567, { decimals: 1 }); // "1,234.6"
 * formatNumber(1234.567, { locale: 'de-DE' }); // "1.234,57"
 * ```
 */
export function formatNumber(
  value: number,
  options: FormatOptions = {}
): string {
  // Merge default options with provided options
  const { decimals, locale } = {
    ...DEFAULT_FORMAT_OPTIONS,
    ...options,
  };

  try {
    return new Intl.NumberFormat(locale, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  } catch (error) {
    console.error('Error formatting number:', error);
    return value.toFixed(decimals);
  }
}

/**
 * Safely parses a JSON string with error handling
 *
 * @param jsonString - The JSON string to parse
 * @param fallback - Optional fallback value if parsing fails
 * @returns Parsed object or fallback value
 *
 * @example
 * ```ts
 * parseJSON('{"name":"John"}'); // { name: 'John' }
 * parseJSON('invalid json', { error: true }); // { error: true }
 * ```
 */
export function parseJSON<T>(jsonString: string, fallback?: T): T | undefined {
  try {
    return JSON.parse(jsonString) as T;
  } catch (error) {
    console.error('Error parsing JSON:', error);
    return fallback;
  }
}

/**
 * Debounces a function call
 *
 * @param fn - The function to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced function
 *
 * @example
 * ```ts
 * const debouncedSearch = debounce((query) => {
 *   searchApi(query);
 * }, 300);
 *
 * // Call multiple times, but only executes once after 300ms
 * debouncedSearch('test');
 * ```
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function(...args: Parameters<T>): void {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Throttles a function call
 *
 * @param fn - The function to throttle
 * @param limit - Time limit in milliseconds
 * @returns Throttled function
 *
 * @example
 * ```ts
 * const throttledScroll = throttle(() => {
 *   updateScrollPosition();
 * }, 100);
 *
 * // Attach to scroll event, will execute at most once every 100ms
 * window.addEventListener('scroll', throttledScroll);
 * ```
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  let lastArgs: Parameters<T> | null = null;

  return function(...args: Parameters<T>): void {
    lastArgs = args;

    if (!inThrottle) {
      fn(...args);
      inThrottle = true;

      setTimeout(() => {
        inThrottle = false;
        if (lastArgs) {
          fn(...lastArgs);
          lastArgs = null;
        }
      }, limit);
    }
  };
}

/**
 * Generates a unique ID with optional prefix
 *
 * @param prefix - Optional prefix for the ID
 * @returns Unique ID string
 *
 * @example
 * ```ts
 * generateId(); // "1a2b3c4d"
 * generateId('user'); // "user_1a2b3c4d"
 * ```
 */
export function generateId(prefix?: string): string {
  const uniquePart = Math.random().toString(36).substring(2, 10);
  return prefix ? `${prefix}_${uniquePart}` : uniquePart;
}

/**
 * Truncates a string to a specified length with ellipsis
 *
 * @param str - The string to truncate
 * @param maxLength - Maximum length before truncation
 * @param ellipsis - String to append when truncated (default: '...')
 * @returns Truncated string
 *
 * @example
 * ```ts
 * truncateString('This is a long text', 10); // "This is a..."
 * truncateString('This is a long text', 10, ' [more]'); // "This is a [more]"
 * ```
 */
export function truncateString(
  str: string,
  maxLength: number,
  ellipsis = '...'
): string {
  if (!str || str.length <= maxLength) {
    return str;
  }

  return str.substring(0, maxLength) + ellipsis;
}

export default {
  formatNumber,
  parseJSON,
  debounce,
  throttle,
  generateId,
  truncateString,
};
