/**
 * Circuit breaker implementation for external service calls
 * 
 * This module provides a circuit breaker pattern implementation to prevent 
 * cascading failures when external services are experiencing issues.
 */

const Brakes = require('brakes');
const { getTracer } = require('../../../../config/tracing-config');
const logger = require('../logger');

// Default circuit breaker configuration
const DEFAULT_CONFIG = {
  name: 'default-circuit',
  // Failure threshold percentage (0-1)
  threshold: 0.5,
  // Number of consecutive failures to trip circuit  
  circuitDuration: 30000,
  // Time in ms circuit stays open before moving to half-open
  timeout: 15000,
  // Request timeout
  statInterval: 10000,
  // Metrics reporting interval
  healthCheckInterval: 15000,
  // Time between health checks when circuit is open
  failureOpenThreshold: 25,
  // Number of failures before circuit opens
  successCloseThreshold: 3,
  // Number of successes needed to close circuit
  fallbackFn: null,
  // Default fallback function
  isFailure: (err) => err !== null && err !== undefined,
  // Override to customize what's considered a failure
  isPromise: true
  // Functions being wrapped return promises
};

// Map to store circuit breaker instances
const circuitInstances = new Map();

// Get tracer for distributed tracing
const tracer = getTracer('circuit-breaker');

/**
 * Create a circuit breaker for an external service
 * 
 * @param {Object} options - Circuit breaker options
 * @param {string} options.name - Unique name for this circuit
 * @param {Function} options.fallbackFn - Function to call when circuit is open
 * @param {number} options.threshold - Failure threshold percentage (0-1)
 * @param {number} options.circuitDuration - Time circuit stays open (ms)
 * @param {number} options.timeout - Request timeout (ms)
 * @param {number} options.failureOpenThreshold - Failures before opening
 * @param {number} options.successCloseThreshold - Successes before closing
 * @returns {Brakes} Circuit breaker instance
 */
function createCircuitBreaker(options) {
  const config = { ...DEFAULT_CONFIG, ...options };
  
  if (!config.name) {
    throw new Error('Circuit breaker name is required');
  }

  // If circuit breaker already exists, return it
  if (circuitInstances.has(config.name)) {
    return circuitInstances.get(config.name);
  }

  // Create a new circuit breaker
  const circuit = new Brakes({
    name: config.name,
    threshold: config.threshold,
    circuitDuration: config.circuitDuration,
    timeout: config.timeout,
    statInterval: config.statInterval,
    healthCheckInterval: config.healthCheckInterval,
    fallbackFn: config.fallbackFn,
    isFailure: config.isFailure,
    isPromise: config.isPromise
  });

  // Add event listeners for metrics and status changes
  circuit.on('snapshot', snapshot => {
    logger.debug('Circuit breaker metrics', {
      circuit: config.name,
      metrics: snapshot
    });
  });

  circuit.on('circuitOpen', () => {
    logger.warn('Circuit breaker opened', {
      circuit: config.name,
      failureCount: circuit.stats.failures
    });
  });

  circuit.on('circuitClosed', () => {
    logger.info('Circuit breaker closed', {
      circuit: config.name
    });
  });

  circuit.on('healthCheckFailed', () => {
    logger.warn('Circuit breaker health check failed', {
      circuit: config.name
    });
  });

  // Store the circuit breaker for reuse
  circuitInstances.set(config.name, circuit);
  return circuit;
}

/**
 * Wrap a function with a circuit breaker
 * 
 * @param {Function} fn - Function to wrap with circuit breaker
 * @param {Object} options - Circuit breaker options
 * @returns {Function} Wrapped function with circuit breaker
 */
function withCircuitBreaker(fn, options) {
  const circuit = createCircuitBreaker(options);
  
  return async function circuitWrappedFn(...args) {
    return tracer.startActiveSpan(`circuit:${options.name}`, async (span) => {
      try {
        span.setAttribute('circuit.name', options.name);
        span.setAttribute('circuit.state', circuit.isOpen() ? 'open' : 'closed');
        
        const result = await circuit.exec(() => fn(...args));
        
        span.setStatus({ code: 0 }); // Success
        span.end();
        
        return result;
      } catch (error) {
        span.setStatus({
          code: 1, // Error
          message: error.message
        });
        span.recordException(error);
        span.end();
        
        throw error;
      }
    });
  };
}

/**
 * Get a specific circuit breaker by name
 * 
 * @param {string} name - Circuit breaker name
 * @returns {Brakes|null} Circuit breaker instance or null if not found
 */
function getCircuitBreaker(name) {
  return circuitInstances.get(name) || null;
}

/**
 * Reset a circuit breaker to its initial state
 * 
 * @param {string} name - Circuit breaker name
 * @returns {boolean} True if reset was successful
 */
function resetCircuit(name) {
  const circuit = circuitInstances.get(name);
  if (circuit) {
    circuit.reset();
    logger.info('Circuit breaker reset', { circuit: name });
    return true;
  }
  return false;
}

/**
 * Get health status of all circuit breakers
 * 
 * @returns {Array<Object>} Array of circuit breaker status objects
 */
function getCircuitHealth() {
  const health = [];
  
  for (const [name, circuit] of circuitInstances.entries()) {
    const stats = circuit.stats;
    health.push({
      name,
      state: circuit.isOpen() ? 'open' : 'closed',
      total: stats.total,
      successful: stats.successful,
      failed: stats.failed,
      timedOut: stats.timedOut,
      percentiles: stats.percentiles,
    });
  }
  
  return health;
}

// Pre-defined circuit breakers for common external services
const externalServices = {
  database: createCircuitBreaker({
    name: 'database',
    threshold: 0.3,
    timeout: 5000,
    fallbackFn: async () => {
      logger.error('Database connection failed, circuit open');
      throw new Error('Database service unavailable');
    }
  }),
  
  emailService: createCircuitBreaker({
    name: 'email-service',
    threshold: 0.4,
    timeout: 10000,
    fallbackFn: async () => {
      logger.error('Email service unavailable, circuit open');
      // Queue for retry later
      return { queued: true, success: false };
    }
  }),
  
  analyticsService: createCircuitBreaker({
    name: 'analytics-service',
    threshold: 0.5,
    timeout: 8000,
    fallbackFn: async () => {
      logger.warn('Analytics service unavailable, circuit open');
      // Return cached or empty data
      return { data: [], cached: true };
    }
  }),
  
  paymentGateway: createCircuitBreaker({
    name: 'payment-gateway',
    threshold: 0.2,  // Lower threshold for critical services
    timeout: 12000,
    fallbackFn: async () => {
      logger.error('Payment gateway unavailable, circuit open');
      throw new Error('Payment service temporarily unavailable');
    }
  }),
  
  authService: createCircuitBreaker({
    name: 'auth-service',
    threshold: 0.3,
    timeout: 5000,
    fallbackFn: async () => {
      logger.error('Auth service unavailable, circuit open');
      throw new Error('Authentication service temporarily unavailable');
    }
  }),
  
  storageService: createCircuitBreaker({
    name: 'storage-service',
    threshold: 0.4,
    timeout: 15000,
    fallbackFn: async () => {
      logger.warn('Storage service unavailable, circuit open');
      throw new Error('Storage service temporarily unavailable');
    }
  }),
  
  aiService: createCircuitBreaker({
    name: 'ai-service',
    threshold: 0.5,
    timeout: 20000,
    fallbackFn: async () => {
      logger.warn('AI service unavailable, circuit open');
      return { success: false, message: 'AI service is temporarily unavailable' };
    }
  }),
};

module.exports = {
  createCircuitBreaker,
  withCircuitBreaker,
  getCircuitBreaker,
  resetCircuit,
  getCircuitHealth,
  externalServices
};
