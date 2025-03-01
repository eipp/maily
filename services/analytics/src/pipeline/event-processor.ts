/**
 * Analytics Event Processing Pipeline
 *
 * This module implements a flexible pipeline for processing analytics events.
 * Events flow through a series of transformers, enrichers, and processors
 * before being stored and analyzed.
 */

import { EventEmitter } from 'events';
import { AnalyticsEvent } from '../index';
import { createLogger } from '../utils/logger';

const logger = createLogger('event-processor');

/**
 * Event processor context
 */
export interface EventProcessorContext {
  /**
   * Event being processed
   */
  event: AnalyticsEvent;

  /**
   * Processing metadata
   */
  meta: Record<string, any>;

  /**
   * Whether to skip storage
   */
  skipStorage?: boolean;

  /**
   * Whether processing was aborted
   */
  aborted?: boolean;

  /**
   * Error that occurred during processing
   */
  error?: Error;
}

/**
 * Type definitions to help with context handling
 */
interface AnalyticsEventContext {
  /**
   * IP address
   */
  ip?: string;

  /**
   * User agent
   */
  userAgent?: string;

  /**
   * User information
   */
  user?: Record<string, any>;

  /**
   * Additional properties
   */
  [key: string]: any;
}

/**
 * Event processor middleware
 */
export type EventProcessorMiddleware = (
  context: EventProcessorContext,
  next: () => Promise<void>
) => Promise<void>;

/**
 * Event processor configuration
 */
export interface EventProcessorConfig {
  /**
   * Maximum concurrency for processing
   */
  concurrency?: number;

  /**
   * Whether to continue processing after errors
   */
  continueOnError?: boolean;

  /**
   * Batch size for processing
   */
  batchSize?: number;

  /**
   * Whether to emit real-time events
   */
  emitRealtime?: boolean;
}

/**
 * Analytics event processing pipeline
 */
export class EventProcessor {
  private middleware: EventProcessorMiddleware[] = [];
  private concurrency: number;
  private continueOnError: boolean;
  private batchSize: number;
  private emitRealtime: boolean;
  private eventEmitter = new EventEmitter();
  private processing = false;
  private queue: AnalyticsEvent[] = [];
  private activeProcessing = 0;

  /**
   * Create an event processor
   * @param config Processor configuration
   */
  constructor(config: EventProcessorConfig = {}) {
    this.concurrency = config.concurrency || 5;
    this.continueOnError = config.continueOnError || false;
    this.batchSize = config.batchSize || 100;
    this.emitRealtime = config.emitRealtime || false;
  }

  /**
   * Use middleware in the processing pipeline
   * @param middleware Middleware function
   * @returns This processor for chaining
   */
  use(middleware: EventProcessorMiddleware): EventProcessor {
    this.middleware.push(middleware);
    return this;
  }

  /**
   * Process an event through the pipeline
   * @param event Event to process
   * @returns Processing result
   */
  async processEvent(event: AnalyticsEvent): Promise<EventProcessorContext> {
    const context: EventProcessorContext = {
      event,
      meta: {},
    };

    // If real-time, emit event
    if (this.emitRealtime) {
      this.eventEmitter.emit('event', event);
    }

    // If no middleware, return immediately
    if (this.middleware.length === 0) {
      return context;
    }

    let index = 0;

    // Create pipeline of middleware
    const runMiddleware = async (): Promise<void> => {
      if (index < this.middleware.length) {
        const currentMiddleware = this.middleware[index];
        index++;

        try {
          await currentMiddleware(context, runMiddleware);
        } catch (error) {
          context.error = error as Error;

          // Log the error
          logger.error('Error in event processing middleware', {
            eventId: event.id,
            eventType: event.type,
            error: (error as Error).message,
            middlewareIndex: index - 1,
          });

          // If not continuing on error, abort
          if (!this.continueOnError) {
            context.aborted = true;
            return;
          }

          // Otherwise, continue to next middleware
          return runMiddleware();
        }
      }
    };

    try {
      await runMiddleware();
    } catch (error) {
      logger.error('Unhandled error in event processing pipeline', {
        eventId: event.id,
        eventType: event.type,
        error: (error as Error).message,
      });

      context.error = error as Error;
      context.aborted = true;
    }

    return context;
  }

  /**
   * Process multiple events in batch
   * @param events Events to process
   * @returns Processing results
   */
  async processBatch(events: AnalyticsEvent[]): Promise<EventProcessorContext[]> {
    const results: EventProcessorContext[] = [];
    const batches: AnalyticsEvent[][] = [];

    // Split into batches
    for (let i = 0; i < events.length; i += this.batchSize) {
      batches.push(events.slice(i, i + this.batchSize));
    }

    // Process batches with concurrency limit
    for (const batch of batches) {
      const batchResults = await Promise.all(
        batch.map(event => this.processEvent(event))
      );

      results.push(...batchResults);
    }

    return results;
  }

  /**
   * Queue an event for processing
   * @param event Event to queue
   */
  queueEvent(event: AnalyticsEvent): void {
    this.queue.push(event);
    this.processQueue();
  }

  /**
   * Queue multiple events for processing
   * @param events Events to queue
   */
  queueEvents(events: AnalyticsEvent[]): void {
    this.queue.push(...events);
    this.processQueue();
  }

  /**
   * Process the event queue
   */
  private async processQueue(): Promise<void> {
    // If already processing or no events, return
    if (this.processing || this.queue.length === 0) {
      return;
    }

    this.processing = true;

    try {
      while (this.queue.length > 0 && this.activeProcessing < this.concurrency) {
        // Get next batch
        const batch = this.queue.splice(0, this.batchSize);
        if (batch.length === 0) break;

        this.activeProcessing++;

        // Process batch asynchronously
        this.processBatch(batch)
          .catch(error => {
            logger.error('Error processing event batch', { error });
          })
          .finally(() => {
            this.activeProcessing--;
            this.processQueue();
          });
      }
    } finally {
      this.processing = false;
    }
  }

  /**
   * Register a listener for real-time events
   * @param listener Event listener
   * @returns Unsubscribe function
   */
  onEvent(listener: (event: AnalyticsEvent) => void): () => void {
    this.eventEmitter.on('event', listener);

    return () => {
      this.eventEmitter.off('event', listener);
    };
  }
}

/**
 * Common middleware factories
 */
export const middleware = {
  /**
   * Log events
   * @param level Log level
   * @returns Middleware
   */
  logger(level: string = 'debug'): EventProcessorMiddleware {
    return async (context, next) => {
      const { event } = context;

      logger.log(level, 'Processing event', {
        id: event.id,
        type: event.type,
        name: event.name,
      });

      await next();

      logger.log(level, 'Processed event', {
        id: event.id,
        type: event.type,
        name: event.name,
        skipped: context.skipStorage,
        error: context.error?.message,
      });
    };
  },

  /**
   * Filter events by criteria
   * @param predicate Filter function
   * @returns Middleware
   */
  filter(predicate: (event: AnalyticsEvent) => boolean): EventProcessorMiddleware {
    return async (context, next) => {
      if (!predicate(context.event)) {
        context.skipStorage = true;
        return;
      }

      await next();
    };
  },

  /**
   * Enrich events with additional data
   * @param enricher Enrichment function
   * @returns Middleware
   */
  enrich(enricher: (event: AnalyticsEvent) => Promise<void>): EventProcessorMiddleware {
    return async (context, next) => {
      await enricher(context.event);
      await next();
    };
  },

  /**
   * Transform events
   * @param transformer Transformation function
   * @returns Middleware
   */
  transform(transformer: (event: AnalyticsEvent) => Promise<AnalyticsEvent>): EventProcessorMiddleware {
    return async (context, next) => {
      context.event = await transformer(context.event);
      await next();
    };
  },

  /**
   * Add user data to events
   * @param userProvider User data provider function
   * @returns Middleware
   */
  addUserData(userProvider: (userId: string) => Promise<Record<string, any>>): EventProcessorMiddleware {
    return async (context, next) => {
      const { event } = context;

      if (event.userId) {
        try {
          const userData = await userProvider(event.userId);

          // Add user data to context
          if (event.context === undefined) {
            event.context = {} as AnalyticsEventContext;
          }

          if (!event.context.user) {
            event.context.user = {};
          }

          event.context.user = { ...event.context.user, ...userData };
        } catch (error) {
          logger.warn('Error fetching user data', {
            userId: event.userId,
            error: (error as Error).message
          });
        }
      }

      await next();
    };
  },

  /**
   * Add geo data to events
   * @param geoProvider Geo data provider function
   * @returns Middleware
   */
  addGeoData(geoProvider: (ip: string) => Promise<Record<string, any>>): EventProcessorMiddleware {
    return async (context, next) => {
      const { event } = context;

      if (event.context && typeof event.context.ip === 'string') {
        try {
          const geoData = await geoProvider(event.context.ip);

          // Add geo data to context
          if (event.context === undefined) {
            event.context = {} as AnalyticsEventContext;
          }

          if (!event.context.geo) {
            event.context.geo = {};
          }

          event.context.geo = { ...event.context.geo, ...geoData };
        } catch (error) {
          logger.warn('Error fetching geo data', {
            ip: event.context.ip,
            error: (error as Error).message
          });
        }
      }

      await next();
    };
  },

  /**
   * Add device data to events
   * @param deviceParser Device parser function
   * @returns Middleware
   */
  addDeviceData(deviceParser: (userAgent: string) => Record<string, any>): EventProcessorMiddleware {
    return async (context, next) => {
      const { event } = context;

      if (event.context && typeof event.context.userAgent === 'string') {
        try {
          const deviceData = deviceParser(event.context.userAgent);

          // Add device data to context
          if (event.context === undefined) {
            event.context = {} as AnalyticsEventContext;
          }

          if (!event.context.device) {
            event.context.device = {};
          }

          event.context.device = { ...event.context.device, ...deviceData };
        } catch (error) {
          logger.warn('Error parsing device data', {
            userAgent: event.context.userAgent,
            error: (error as Error).message
          });
        }
      }

      await next();
    };
  },

  /**
   * Rate limit events by key
   * @param getKey Key function
   * @param maxEvents Maximum events per window
   * @param windowMs Window size in milliseconds
   * @returns Middleware
   */
  rateLimit(
    getKey: (event: AnalyticsEvent) => string,
    maxEvents: number = 100,
    windowMs: number = 60000
  ): EventProcessorMiddleware {
    const windows = new Map<string, number[]>();

    return async (context, next) => {
      const { event } = context;
      const key = getKey(event);
      const now = Date.now();

      // Get or create window
      let timestamps = windows.get(key);
      if (!timestamps) {
        timestamps = [];
        windows.set(key, timestamps);
      }

      // Remove expired timestamps
      const windowStart = now - windowMs;
      while (timestamps.length > 0 && timestamps[0] < windowStart) {
        timestamps.shift();
      }

      // Check if rate limited
      if (timestamps.length >= maxEvents) {
        context.skipStorage = true;
        return;
      }

      // Add current timestamp
      timestamps.push(now);

      await next();
    };
  },
};

export default EventProcessor;
