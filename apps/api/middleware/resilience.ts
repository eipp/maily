/**
 * Resilience Middleware
 * 
 * This middleware implements circuit breakers for external dependencies using Resilience4j.
 * It provides retry mechanisms with exponential backoff and graceful degradation for non-critical features.
 */

import { NextFunction, Request, Response } from 'express';
import { CircuitBreaker, CircuitBreakerOptions } from 'resilience4j-circuitbreaker';
import { Retry, RetryOptions } from 'resilience4j-retry';
import { Bulkhead, BulkheadOptions } from 'resilience4j-bulkhead';
import { logger } from '../utils/logger';
import { ApiError } from '../utils/api-error';

// Environment variables
const RESILIENCE_ENABLED = process.env.RESILIENCE_ENABLED !== 'false';

// Circuit breaker configurations for different services
const circuitBreakerConfigs: Record<string, CircuitBreakerOptions> = {
  database: {
    failureRateThreshold: 50,
    slowCallRateThreshold: 50,
    slowCallDurationThreshold: 1000,
    permittedNumberOfCallsInHalfOpenState: 10,
    slidingWindowSize: 100,
    slidingWindowType: 'COUNT_BASED',
    minimumNumberOfCalls: 10,
    waitDurationInOpenState: 60000,
    automaticTransitionFromOpenToHalfOpenEnabled: true,
  },
  email: {
    failureRateThreshold: 50,
    slowCallRateThreshold: 50,
    slowCallDurationThreshold: 2000,
    permittedNumberOfCallsInHalfOpenState: 5,
    slidingWindowSize: 50,
    slidingWindowType: 'COUNT_BASED',
    minimumNumberOfCalls: 5,
    waitDurationInOpenState: 30000,
    automaticTransitionFromOpenToHalfOpenEnabled: true,
  },
  analytics: {
    failureRateThreshold: 70,
    slowCallRateThreshold: 70,
    slowCallDurationThreshold: 3000,
    permittedNumberOfCallsInHalfOpenState: 3,
    slidingWindowSize: 30,
    slidingWindowType: 'COUNT_BASED',
    minimumNumberOfCalls: 3,
    waitDurationInOpenState: 15000,
    automaticTransitionFromOpenToHalfOpenEnabled: true,
  },
  ai: {
    failureRateThreshold: 60,
    slowCallRateThreshold: 60,
    slowCallDurationThreshold: 5000,
    permittedNumberOfCallsInHalfOpenState: 5,
    slidingWindowSize: 50,
    slidingWindowType: 'COUNT_BASED',
    minimumNumberOfCalls: 5,
    waitDurationInOpenState: 30000,
    automaticTransitionFromOpenToHalfOpenEnabled: true,
  },
  blockchain: {
    failureRateThreshold: 50,
    slowCallRateThreshold: 50,
    slowCallDurationThreshold: 10000,
    permittedNumberOfCallsInHalfOpenState: 3,
    slidingWindowSize: 30,
    slidingWindowType: 'COUNT_BASED',
    minimumNumberOfCalls: 3,
    waitDurationInOpenState: 60000,
    automaticTransitionFromOpenToHalfOpenEnabled: true,
  },
};

// Default circuit breaker configuration
const defaultCircuitBreakerConfig: CircuitBreakerOptions = {
  failureRateThreshold: 50,
  slowCallRateThreshold: 50,
  slowCallDurationThreshold: 2000,
  permittedNumberOfCallsInHalfOpenState: 5,
  slidingWindowSize: 50,
  slidingWindowType: 'COUNT_BASED',
  minimumNumberOfCalls: 5,
  waitDurationInOpenState: 30000,
  automaticTransitionFromOpenToHalfOpenEnabled: true,
};

// Retry configurations for different services
const retryConfigs: Record<string, RetryOptions> = {
  database: {
    maxAttempts: 3,
    waitDuration: 1000,
    intervalFunction: (attempt) => Math.pow(2, attempt) * 1000, // Exponential backoff
  },
  email: {
    maxAttempts: 5,
    waitDuration: 2000,
    intervalFunction: (attempt) => Math.pow(1.5, attempt) * 2000,
  },
  analytics: {
    maxAttempts: 2,
    waitDuration: 1000,
    intervalFunction: (attempt) => Math.pow(2, attempt) * 1000,
  },
  ai: {
    maxAttempts: 3,
    waitDuration: 2000,
    intervalFunction: (attempt) => Math.pow(2, attempt) * 2000,
  },
  blockchain: {
    maxAttempts: 5,
    waitDuration: 5000,
    intervalFunction: (attempt) => Math.pow(1.5, attempt) * 5000,
  },
};

// Default retry configuration
const defaultRetryConfig: RetryOptions = {
  maxAttempts: 3,
  waitDuration: 1000,
  intervalFunction: (attempt) => Math.pow(2, attempt) * 1000,
};

// Bulkhead configurations for different services
const bulkheadConfigs: Record<string, BulkheadOptions> = {
  database: {
    maxConcurrentCalls: 50,
    maxWaitDuration: 1000,
  },
  email: {
    maxConcurrentCalls: 20,
    maxWaitDuration: 2000,
  },
  analytics: {
    maxConcurrentCalls: 10,
    maxWaitDuration: 500,
  },
  ai: {
    maxConcurrentCalls: 5,
    maxWaitDuration: 5000,
  },
  blockchain: {
    maxConcurrentCalls: 5,
    maxWaitDuration: 10000,
  },
};

// Default bulkhead configuration
const defaultBulkheadConfig: BulkheadOptions = {
  maxConcurrentCalls: 20,
  maxWaitDuration: 1000,
};

// Circuit breakers for different services
const circuitBreakers: Record<string, CircuitBreaker> = {};

// Retries for different services
const retries: Record<string, Retry> = {};

// Bulkheads for different services
const bulkheads: Record<string, Bulkhead> = {};

/**
 * Initialize resilience components
 */
const initializeResilience = () => {
  if (!RESILIENCE_ENABLED) {
    logger.info('Resilience is disabled');
    return;
  }
  
  // Initialize circuit breakers for each service
  for (const [service, config] of Object.entries(circuitBreakerConfigs)) {
    circuitBreakers[service] = new CircuitBreaker(service, config);
    
    // Register event listeners
    circuitBreakers[service].on('success', () => {
      logger.debug(`Circuit breaker ${service}: success`);
    });
    
    circuitBreakers[service].on('error', (error) => {
      logger.warn(`Circuit breaker ${service}: error`, error);
    });
    
    circuitBreakers[service].on('state_transition', (oldState, newState) => {
      logger.info(`Circuit breaker ${service}: ${oldState} -> ${newState}`);
    });
  }
  
  // Initialize retries for each service
  for (const [service, config] of Object.entries(retryConfigs)) {
    retries[service] = new Retry(service, config);
    
    // Register event listeners
    retries[service].on('success', (result, attempt) => {
      if (attempt > 1) {
        logger.info(`Retry ${service}: success after ${attempt} attempts`);
      }
    });
    
    retries[service].on('error', (error, attempt) => {
      logger.warn(`Retry ${service}: error on attempt ${attempt}`, error);
    });
  }
  
  // Initialize bulkheads for each service
  for (const [service, config] of Object.entries(bulkheadConfigs)) {
    bulkheads[service] = new Bulkhead(service, config);
    
    // Register event listeners
    bulkheads[service].on('call_rejected', () => {
      logger.warn(`Bulkhead ${service}: call rejected`);
    });
    
    bulkheads[service].on('call_finished', () => {
      logger.debug(`Bulkhead ${service}: call finished`);
    });
  }
  
  logger.info('Resilience components initialized');
};

// Initialize resilience components on module load
initializeResilience();

/**
 * Get circuit breaker for service
 * 
 * @param service Service name
 * @returns Circuit breaker
 */
export const getCircuitBreaker = (service: string): CircuitBreaker => {
  return circuitBreakers[service] || new CircuitBreaker(service, defaultCircuitBreakerConfig);
};

/**
 * Get retry for service
 * 
 * @param service Service name
 * @returns Retry
 */
export const getRetry = (service: string): Retry => {
  return retries[service] || new Retry(service, defaultRetryConfig);
};

/**
 * Get bulkhead for service
 * 
 * @param service Service name
 * @returns Bulkhead
 */
export const getBulkhead = (service: string): Bulkhead => {
  return bulkheads[service] || new Bulkhead(service, defaultBulkheadConfig);
};

/**
 * Execute function with resilience
 * 
 * @param service Service name
 * @param fn Function to execute
 * @param fallback Fallback function
 * @returns Function result
 */
export const executeWithResilience = async <T>(
  service: string,
  fn: () => Promise<T>,
  fallback?: () => Promise<T>
): Promise<T> => {
  if (!RESILIENCE_ENABLED) {
    return fn();
  }
  
  const circuitBreaker = getCircuitBreaker(service);
  const retry = getRetry(service);
  const bulkhead = getBulkhead(service);
  
  try {
    // Execute function with resilience
    return await bulkhead.executeFunction(async () => {
      return await retry.executeFunction(async () => {
        return await circuitBreaker.executeFunction(fn);
      });
    });
  } catch (error) {
    // If fallback is provided, use it
    if (fallback) {
      logger.warn(`Executing fallback for ${service}`);
      return fallback();
    }
    
    // Otherwise, rethrow the error
    throw error;
  }
};

/**
 * Resilience middleware for specific service
 * 
 * @param service Service name
 * @param options Options
 * @returns Express middleware
 */
export const resilienceMiddleware = (
  service: string,
  options: {
    fallback?: (req: Request, res: Response, next: NextFunction) => void;
    isCritical?: boolean;
  } = {}
) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (!RESILIENCE_ENABLED) {
      return next();
    }
    
    const circuitBreaker = getCircuitBreaker(service);
    
    // Check if circuit breaker is open
    if (circuitBreaker.getState() === 'OPEN') {
      // If service is critical, return error
      if (options.isCritical !== false) {
        return next(new ApiError(503, 'Service Unavailable', `${service} service is currently unavailable`));
      }
      
      // If fallback is provided, use it
      if (options.fallback) {
        return options.fallback(req, res, next);
      }
      
      // Otherwise, continue with degraded functionality
      req.serviceUnavailable = req.serviceUnavailable || {};
      req.serviceUnavailable[service] = true;
      
      return next();
    }
    
    // Continue with normal flow
    next();
  };
};

/**
 * Health check middleware
 * 
 * @returns Express middleware
 */
export const healthCheckMiddleware = () => {
  return (req: Request, res: Response) => {
    const health = {
      status: 'UP',
      timestamp: new Date().toISOString(),
      services: {} as Record<string, any>,
    };
    
    // Check circuit breakers
    for (const [service, circuitBreaker] of Object.entries(circuitBreakers)) {
      health.services[service] = {
        status: circuitBreaker.getState() === 'CLOSED' ? 'UP' : 'DOWN',
        state: circuitBreaker.getState(),
        metrics: {
          failureRate: circuitBreaker.getMetrics().getFailureRate(),
          slowCallRate: circuitBreaker.getMetrics().getSlowCallRate(),
          numberOfCalls: circuitBreaker.getMetrics().getNumberOfCalls(),
          numberOfFailedCalls: circuitBreaker.getMetrics().getNumberOfFailedCalls(),
          numberOfSlowCalls: circuitBreaker.getMetrics().getNumberOfSlowCalls(),
        },
      };
      
      // Update overall status
      if (circuitBreaker.getState() !== 'CLOSED' && health.status === 'UP') {
        health.status = 'DEGRADED';
      }
    }
    
    // Return health check response
    res.status(health.status === 'UP' ? 200 : 503).json(health);
  };
};

/**
 * Cleanup resilience resources
 */
export const cleanupResilience = () => {
  // No cleanup needed for resilience components
};

// Extend Express Request interface
declare global {
  namespace Express {
    interface Request {
      serviceUnavailable?: Record<string, boolean>;
    }
  }
}

export default resilienceMiddleware;
