/**
 * Common utility functions used across the application
 */

/**
 * Deep clone an object
 * @param obj - The object to clone
 * @returns A deep clone of the object
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T;
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as unknown as T;
  }

  if (obj instanceof Object) {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [key, deepClone(value)])
    ) as unknown as T;
  }

  return obj;
}

/**
 * Generate a UUID v4
 * @returns A UUID v4 string
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Create a debounced function
 * @param func - The function to debounce
 * @param wait - The debounce wait time in ms
 * @param immediate - Whether to call the function immediately
 * @returns A debounced version of the function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait = 300,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function(this: any, ...args: Parameters<T>): void {
    const context = this;

    const later = function() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };

    const callNow = immediate && !timeout;

    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);

    if (callNow) func.apply(context, args);
  };
}

/**
 * Create a throttled function
 * @param func - The function to throttle
 * @param limit - The throttle limit in ms
 * @returns A throttled version of the function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit = 300
): (...args: Parameters<T>) => void {
  let inThrottle = false;

  return function(this: any, ...args: Parameters<T>): void {
    const context = this;

    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

/**
 * Compose multiple functions into a single function
 * @param funcs - Functions to compose (executed right to left)
 * @returns Composed function
 */
export function compose<T>(...funcs: Array<(arg: T) => T>): (arg: T) => T {
  return (arg: T) => funcs.reduceRight((acc, fn) => fn(acc), arg);
}

/**
 * Pipe a value through multiple functions
 * @param funcs - Functions to pipe through (executed left to right)
 * @returns Piped function
 */
export function pipe<T>(...funcs: Array<(arg: T) => T>): (arg: T) => T {
  return (arg: T) => funcs.reduce((acc, fn) => fn(acc), arg);
}

/**
 * Check if a value is undefined or null
 * @param value - The value to check
 * @returns True if the value is undefined or null
 */
export function isNil(value: any): value is null | undefined {
  return value === undefined || value === null;
}

/**
 * Get a value from an object by path
 * @param obj - The object to get the value from
 * @param path - The path to the value (e.g., 'user.address.street')
 * @param defaultValue - The default value to return if the path doesn't exist
 * @returns The value at the path or the default value
 */
export function get<T>(
  obj: Record<string, any>,
  path: string,
  defaultValue?: T
): T | undefined {
  const keys = path.split('.');
  let result: any = obj;

  for (const key of keys) {
    if (result === undefined || result === null) {
      return defaultValue;
    }
    result = result[key];
  }

  return (result === undefined ? defaultValue : result) as T | undefined;
}

/**
 * Set a value in an object by path
 * @param obj - The object to set the value in
 * @param path - The path to set the value at (e.g., 'user.address.street')
 * @param value - The value to set
 * @returns The modified object
 */
export function set<T extends Record<string, any>>(
  obj: T,
  path: string,
  value: any
): T {
  const keys = path.split('.');
  const result = { ...obj };
  let current: any = result;

  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];

    if (i === keys.length - 1) {
      current[key] = value;
    } else {
      current[key] = current[key] === undefined || current[key] === null
        ? {}
        : { ...current[key] };
      current = current[key];
    }
  }

  return result;
}

/**
 * Group an array of objects by a key
 * @param array - The array to group
 * @param key - The key to group by
 * @returns An object with keys as group values and values as arrays of items
 */
export function groupBy<T>(
  array: T[],
  key: keyof T
): Record<string, T[]> {
  return array.reduce((result, item) => {
    const group = String(item[key]);
    result[group] = result[group] || [];
    result[group].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * Chunk an array into smaller arrays of a specified size
 * @param array - The array to chunk
 * @param size - The size of each chunk
 * @returns An array of chunks
 */
export function chunk<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

/**
 * Retry a function with exponential backoff
 * @param fn - The function to retry
 * @param options - Retry options
 * @returns A promise that resolves when the function succeeds
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
    factor?: number;
    onRetry?: (attempt: number, error: Error) => void;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    factor = 2,
    onRetry = () => {},
  } = options;

  let attempt = 0;
  let delay = initialDelay;

  while (true) {
    try {
      return await fn();
    } catch (error) {
      attempt++;

      if (attempt >= maxRetries) {
        throw error;
      }

      if (error instanceof Error) {
        onRetry(attempt, error);
      }

      // Wait for the backoff delay
      await new Promise(resolve => setTimeout(resolve, delay));

      // Increase delay for next attempt (with maximum limit)
      delay = Math.min(delay * factor, maxDelay);
    }
  }
}

/**
 * Sleep for a specified duration
 * @param ms - The number of milliseconds to sleep
 * @returns A promise that resolves after the specified duration
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Memoize a function (cache its results)
 * @param fn - The function to memoize
 * @returns A memoized version of the function
 */
export function memoize<T extends (...args: any[]) => any>(
  fn: T
): T {
  const cache = new Map();

  return function(this: any, ...args: Parameters<T>): ReturnType<T> {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = fn.apply(this, args);
    cache.set(key, result);

    return result;
  } as T;
}

/**
 * Create a function that runs only once
 * @param fn - The function to run once
 * @returns A function that will only call the original function once
 */
export function once<T extends (...args: any[]) => any>(
  fn: T
): (...args: Parameters<T>) => ReturnType<T> {
  let called = false;
  let result: ReturnType<T>;

  return function(this: any, ...args: Parameters<T>): ReturnType<T> {
    if (!called) {
      called = true;
      result = fn.apply(this, args);
    }
    return result;
  };
}
