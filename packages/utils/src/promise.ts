/**
 * Promise utility functions
 */

/**
 * Delay for a specified number of milliseconds
 * @param ms Milliseconds to delay
 * @returns Promise that resolves after the delay
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Timeout a promise after a specified duration
 * @param promise Promise to timeout
 * @param ms Timeout duration in milliseconds
 * @param errorMessage Error message for timeout
 * @returns Promise with timeout
 */
export function timeout<T>(
  promise: Promise<T>,
  ms: number,
  errorMessage: string = 'Operation timed out'
): Promise<T> {
  // Create a timeout promise that rejects after ms
  const timeoutPromise = new Promise<never>((_, reject) => {
    const timeoutId = setTimeout(() => {
      clearTimeout(timeoutId);
      reject(new Error(errorMessage));
    }, ms);
  });

  // Race the original promise against the timeout
  return Promise.race([promise, timeoutPromise]);
}

/**
 * Retry a function with exponential backoff
 * @param fn Function to retry
 * @param options Retry options
 * @returns Promise that resolves when function succeeds or max attempts reached
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffFactor?: number;
    shouldRetry?: (error: any) => boolean;
    onRetry?: (error: any, attempt: number, delay: number) => void;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 200,
    maxDelay = 5000,
    backoffFactor = 2,
    shouldRetry = () => true,
    onRetry,
  } = options;

  let lastError: any;
  let currentDelay = initialDelay;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt === maxAttempts || !shouldRetry(error)) {
        throw error;
      }

      if (onRetry) {
        onRetry(error, attempt, currentDelay);
      }

      await delay(currentDelay);

      // Calculate next delay with exponential backoff
      currentDelay = Math.min(currentDelay * backoffFactor, maxDelay);
    }
  }

  throw lastError;
}

/**
 * Run promises sequentially
 * @param fns Array of functions that return promises
 * @returns Promise that resolves with array of results
 */
export async function sequence<T>(fns: Array<() => Promise<T>>): Promise<T[]> {
  const results: T[] = [];

  for (const fn of fns) {
    results.push(await fn());
  }

  return results;
}

/**
 * Run promises in parallel with concurrency limit
 * @param fns Array of functions that return promises
 * @param concurrency Maximum number of concurrent promises
 * @returns Promise that resolves with array of results
 */
export async function parallel<T>(
  fns: Array<() => Promise<T>>,
  concurrency: number = Infinity
): Promise<T[]> {
  if (!fns.length) {
    return [];
  }

  const results: T[] = [];
  const executing: Set<Promise<unknown>> = new Set();

  // Make a copy of the array to avoid modifying the original
  const queue = [...fns];

  return new Promise((resolve, reject) => {
    const checkComplete = () => {
      if (queue.length === 0 && executing.size === 0) {
        resolve(results);
      }
    };

    const runTask = async (taskFn: () => Promise<T>, index: number) => {
      const promise = Promise.resolve().then(() => taskFn());
      executing.add(promise);

      try {
        const result = await promise;
        results[index] = result;
      } catch (error) {
        reject(error);
      } finally {
        executing.delete(promise);

        if (queue.length > 0) {
          const nextIndex = fns.length - queue.length;
          const nextTask = queue.shift()!;
          runTask(nextTask, nextIndex);
        } else {
          checkComplete();
        }
      }
    };

    // Start initial tasks up to concurrency limit
    const initialTasks = Math.min(concurrency, queue.length);
    for (let i = 0; i < initialTasks; i++) {
      const taskFn = queue.shift()!;
      runTask(taskFn, i);
    }

    // Handle empty array case
    checkComplete();
  });
}

/**
 * Run promises in batches
 * @param fns Array of functions that return promises
 * @param batchSize Number of promises per batch
 * @param batchDelay Delay between batches in milliseconds
 * @returns Promise that resolves with array of results
 */
export async function batch<T>(
  fns: Array<() => Promise<T>>,
  batchSize: number = 5,
  batchDelay: number = 0
): Promise<T[]> {
  const results: T[] = [];

  for (let i = 0; i < fns.length; i += batchSize) {
    const batchFns = fns.slice(i, i + batchSize);
    const batchResults = await Promise.all(batchFns.map(fn => fn()));
    results.push(...batchResults);

    if (batchDelay > 0 && i + batchSize < fns.length) {
      await delay(batchDelay);
    }
  }

  return results;
}

/**
 * Create a deferred promise
 * @returns Deferred promise with resolve and reject functions
 */
export function deferred<T>(): {
  promise: Promise<T>;
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: any) => void;
} {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: any) => void;

  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, resolve, reject };
}

/**
 * Create a cancelable promise
 * @param executor Promise executor function
 * @returns Cancelable promise
 */
export function cancelable<T>(
  executor: (
    resolve: (value: T | PromiseLike<T>) => void,
    reject: (reason?: any) => void,
    signal: AbortSignal
  ) => void
): { promise: Promise<T>; cancel: (reason?: any) => void } {
  const controller = new AbortController();
  const { signal } = controller;

  const promise = new Promise<T>((resolve, reject) => {
    // Handle abort event
    signal.addEventListener('abort', () => {
      reject(signal.reason || new Error('Promise canceled'));
    });

    // Call executor with signal
    executor(resolve, reject, signal);
  });

  return {
    promise,
    cancel: (reason?: any) => {
      controller.abort(reason);
    },
  };
}

/**
 * Pool for limiting concurrent promises
 */
export class PromisePool {
  private limit: number;
  private executing: Set<Promise<any>>;
  private queue: Array<() => void>;

  /**
   * Create a new promise pool
   * @param concurrency Maximum number of concurrent promises
   */
  constructor(concurrency: number = 5) {
    this.limit = concurrency;
    this.executing = new Set();
    this.queue = [];
  }

  /**
   * Add a task to the pool
   * @param fn Function that returns a promise
   * @returns Promise for the task result
   */
  async add<T>(fn: () => Promise<T>): Promise<T> {
    // Wait until we're below the concurrency limit
    if (this.executing.size >= this.limit) {
      await new Promise<void>(resolve => {
        this.queue.push(resolve);
      });
    }

    // Execute the task
    const promise = Promise.resolve().then(fn);
    this.executing.add(promise);

    try {
      return await promise;
    } finally {
      this.executing.delete(promise);

      // Allow the next task to execute
      if (this.queue.length > 0) {
        const next = this.queue.shift()!;
        next();
      }
    }
  }

  /**
   * Wait for all tasks to complete
   * @returns Promise that resolves when all tasks are complete
   */
  async wait(): Promise<void> {
    if (this.executing.size === 0) {
      return;
    }

    await Promise.all(Array.from(this.executing));
  }
}

/**
 * Cache function results with TTL
 * @param fn Function to cache
 * @param options Cache options
 * @returns Cached function
 */
export function memoizePromise<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: {
    ttl?: number;
    cacheKey?: (...args: Parameters<T>) => string;
    maxSize?: number;
  } = {}
): T {
  const {
    ttl = 0, // 0 means no expiration
    cacheKey = (...args: Parameters<T>) => JSON.stringify(args),
    maxSize = 100,
  } = options;

  // Cache entries with expiration
  interface CacheEntry {
    value: any;
    expires: number | null;
  }

  const cache = new Map<string, CacheEntry>();
  const timestamps = new Map<string, number>();

  const cachedFn = async (...args: Parameters<T>) => {
    const key = cacheKey(...args);
    const now = Date.now();

    // Check if we have a cached entry
    if (cache.has(key)) {
      const entry = cache.get(key)!;

      // Check if the entry is still valid
      if (!entry.expires || entry.expires > now) {
        // Update access timestamp
        timestamps.set(key, now);
        return entry.value;
      }

      // Delete expired entry
      cache.delete(key);
      timestamps.delete(key);
    }

    // Execute the function
    const result = await fn(...args);

    // Store the result in cache
    cache.set(key, {
      value: result,
      expires: ttl > 0 ? now + ttl : null,
    });

    // Update access timestamp
    timestamps.set(key, now);

    // Enforce max size
    if (maxSize > 0 && cache.size > maxSize) {
      // Find the least recently used entry
      let oldestKey = '';
      let oldestTime = Infinity;

      for (const [k, time] of timestamps.entries()) {
        if (time < oldestTime) {
          oldestTime = time;
          oldestKey = k;
        }
      }

      // Remove the oldest entry
      if (oldestKey) {
        cache.delete(oldestKey);
        timestamps.delete(oldestKey);
      }
    }

    return result;
  };

  // Add a method to clear the cache
  (cachedFn as any).clearCache = () => {
    cache.clear();
    timestamps.clear();
  };

  return cachedFn as T;
}

/**
 * Run a function with a semaphore
 */
export class Semaphore {
  private permits: number;
  private queue: Array<() => void> = [];

  /**
   * Create a new semaphore
   * @param permits Number of concurrent operations allowed
   */
  constructor(permits: number = 1) {
    this.permits = permits;
  }

  /**
   * Run a function with the semaphore
   * @param fn Function to run
   * @returns Promise for the function result
   */
  async run<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();

    try {
      return await fn();
    } finally {
      this.release();
    }
  }

  /**
   * Acquire a permit
   * @returns Promise that resolves when a permit is available
   */
  private acquire(): Promise<void> {
    if (this.permits > 0) {
      this.permits--;
      return Promise.resolve();
    }

    return new Promise<void>(resolve => {
      this.queue.push(resolve);
    });
  }

  /**
   * Release a permit
   */
  private release(): void {
    const next = this.queue.shift();

    if (next) {
      // Someone is waiting, give them the permit
      next();
    } else {
      // No one waiting, add permit back to pool
      this.permits++;
    }
  }

  /**
   * Get the number of available permits
   */
  get available(): number {
    return this.permits;
  }

  /**
   * Get the number of queued operations
   */
  get queueLength(): number {
    return this.queue.length;
  }
}
