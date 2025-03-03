/**
 * Retry utility for handling transient failures
 * 
 * This module provides a retry function that can be used to retry operations
 * that may fail due to transient issues, such as network connectivity problems
 * or temporary service unavailability.
 */

import { logger } from './logger';

/**
 * Retry a function with exponential backoff
 * 
 * @param fn Function to retry
 * @param maxRetries Maximum number of retry attempts
 * @param initialDelay Initial delay in milliseconds
 * @param backoffFactor Factor to multiply delay by after each retry (default: 2)
 * @param maxDelay Maximum delay in milliseconds (default: 30000)
 * @returns Result of the function
 * @throws Error if all retry attempts fail
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number,
  initialDelay: number,
  backoffFactor: number = 2,
  maxDelay: number = 30000
): Promise<T> {
  let lastError: Error | null = null;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // If this is a retry attempt, log it
      if (attempt > 0) {
        logger.info(`Retry attempt ${attempt}/${maxRetries} after ${delay}ms delay`);
      }

      // Execute the function
      return await fn();
    } catch (error) {
      // Save the error for potential re-throw
      lastError = error;

      // If we've exhausted all retries, break out of the loop
      if (attempt >= maxRetries) {
        break;
      }

      // Log the error
      logger.warn(`Attempt ${attempt + 1}/${maxRetries} failed: ${error.message}`);

      // Wait before the next retry
      await new Promise(resolve => setTimeout(resolve, delay));

      // Increase the delay for the next retry (with a maximum limit)
      delay = Math.min(delay * backoffFactor, maxDelay);
    }
  }

  // If we get here, all retries have failed
  logger.error(`All ${maxRetries} retry attempts failed`);
  throw lastError || new Error('All retry attempts failed');
}

/**
 * Retry a function with exponential backoff and custom retry condition
 * 
 * @param fn Function to retry
 * @param shouldRetry Function that determines if a retry should be attempted based on the error
 * @param maxRetries Maximum number of retry attempts
 * @param initialDelay Initial delay in milliseconds
 * @param backoffFactor Factor to multiply delay by after each retry (default: 2)
 * @param maxDelay Maximum delay in milliseconds (default: 30000)
 * @returns Result of the function
 * @throws Error if all retry attempts fail or if shouldRetry returns false
 */
export async function retryWithCondition<T>(
  fn: () => Promise<T>,
  shouldRetry: (error: Error) => boolean,
  maxRetries: number,
  initialDelay: number,
  backoffFactor: number = 2,
  maxDelay: number = 30000
): Promise<T> {
  let lastError: Error | null = null;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // If this is a retry attempt, log it
      if (attempt > 0) {
        logger.info(`Retry attempt ${attempt}/${maxRetries} after ${delay}ms delay`);
      }

      // Execute the function
      return await fn();
    } catch (error) {
      // Save the error for potential re-throw
      lastError = error;

      // Check if we should retry based on the error
      if (!shouldRetry(error)) {
        logger.info(`Not retrying: ${error.message}`);
        throw error;
      }

      // If we've exhausted all retries, break out of the loop
      if (attempt >= maxRetries) {
        break;
      }

      // Log the error
      logger.warn(`Attempt ${attempt + 1}/${maxRetries} failed: ${error.message}`);

      // Wait before the next retry
      await new Promise(resolve => setTimeout(resolve, delay));

      // Increase the delay for the next retry (with a maximum limit)
      delay = Math.min(delay * backoffFactor, maxDelay);
    }
  }

  // If we get here, all retries have failed
  logger.error(`All ${maxRetries} retry attempts failed`);
  throw lastError || new Error('All retry attempts failed');
}

/**
 * Retry a function with jitter to avoid thundering herd problem
 * 
 * @param fn Function to retry
 * @param maxRetries Maximum number of retry attempts
 * @param initialDelay Initial delay in milliseconds
 * @param backoffFactor Factor to multiply delay by after each retry (default: 2)
 * @param maxDelay Maximum delay in milliseconds (default: 30000)
 * @param jitterFactor Factor to apply random jitter (default: 0.2)
 * @returns Result of the function
 * @throws Error if all retry attempts fail
 */
export async function retryWithJitter<T>(
  fn: () => Promise<T>,
  maxRetries: number,
  initialDelay: number,
  backoffFactor: number = 2,
  maxDelay: number = 30000,
  jitterFactor: number = 0.2
): Promise<T> {
  let lastError: Error | null = null;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // If this is a retry attempt, log it
      if (attempt > 0) {
        logger.info(`Retry attempt ${attempt}/${maxRetries} after ${delay}ms delay`);
      }

      // Execute the function
      return await fn();
    } catch (error) {
      // Save the error for potential re-throw
      lastError = error;

      // If we've exhausted all retries, break out of the loop
      if (attempt >= maxRetries) {
        break;
      }

      // Log the error
      logger.warn(`Attempt ${attempt + 1}/${maxRetries} failed: ${error.message}`);

      // Calculate jitter
      const jitter = delay * jitterFactor * (Math.random() * 2 - 1);
      const delayWithJitter = Math.max(0, delay + jitter);

      // Wait before the next retry
      await new Promise(resolve => setTimeout(resolve, delayWithJitter));

      // Increase the delay for the next retry (with a maximum limit)
      delay = Math.min(delay * backoffFactor, maxDelay);
    }
  }

  // If we get here, all retries have failed
  logger.error(`All ${maxRetries} retry attempts failed`);
  throw lastError || new Error('All retry attempts failed');
}
