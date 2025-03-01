/**
 * Analytics Service
 *
 * This service handles analytics event processing, storage, and querying.
 * It uses an event-driven architecture to process high-volume analytics data
 * with reliability and scalability.
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from './utils/logger';

const logger = createLogger('analytics-service');

/**
 * Event type definitions
 */
export type EventType =
  | 'page_view'
  | 'click'
  | 'form_submit'
  | 'feature_usage'
  | 'error'
  | 'performance'
  | 'conversion'
  | 'campaign_interaction'
  | 'session_start'
  | 'session_end'
  | 'custom';

/**
 * Basic analytics event structure
 */
export interface AnalyticsEvent {
  /**
   * Unique event ID
   */
  id: string;

  /**
   * Event type
   */
  type: EventType;

  /**
   * Event name
   */
  name: string;

  /**
   * Event timestamp
   */
  timestamp: Date;

  /**
   * Associated user ID (if authenticated)
   */
  userId?: string;

  /**
   * Anonymous session ID
   */
  sessionId?: string;

  /**
   * Event properties
   */
  properties?: Record<string, any>;

  /**
   * Event context information
   */
  context?: {
    /**
     * User agent string
     */
    userAgent?: string;

    /**
     * IP address
     */
    ip?: string;

    /**
     * Page URL
     */
    url?: string;

    /**
     * Referrer URL
     */
    referrer?: string;

    /**
     * Device type
     */
    device?: string;

    /**
     * Browser name and version
     */
    browser?: string;

    /**
     * Operating system
     */
    os?: string;

    /**
     * Locale
     */
    locale?: string;

    /**
     * Screen resolution
     */
    screen?: string;

    /**
     * UTM parameters
     */
    utm?: {
      source?: string;
      medium?: string;
      campaign?: string;
      term?: string;
      content?: string;
    };

    /**
     * Additional context data
     */
    [key: string]: any;
  };

  /**
   * Source of the event
   */
  source?: string;
}

/**
 * Analytics storage provider interface
 */
export interface AnalyticsStorageProvider {
  /**
   * Store an analytics event
   * @param event Analytics event to store
   * @returns Promise resolving when event is stored
   */
  storeEvent(event: AnalyticsEvent): Promise<void>;

  /**
   * Query analytics events
   * @param query Query parameters
   * @returns Promise resolving to matching events
   */
  queryEvents(query: AnalyticsQuery): Promise<AnalyticsQueryResult>;

  /**
   * Get aggregated metrics
   * @param metric Metric to aggregate
   * @param dimensions Dimensions to group by
   * @param filters Filters to apply
   * @param timeframe Timeframe to query
   * @returns Promise resolving to aggregated metrics
   */
  getMetrics(
    metric: string,
    dimensions: string[],
    filters: Record<string, any>,
    timeframe: TimeFrame
  ): Promise<AggregatedMetrics>;
}

/**
 * Analytics query parameters
 */
export interface AnalyticsQuery {
  /**
   * Event types to include
   */
  eventTypes?: EventType[];

  /**
   * Event names to include
   */
  eventNames?: string[];

  /**
   * User IDs to include
   */
  userIds?: string[];

  /**
   * Session IDs to include
   */
  sessionIds?: string[];

  /**
   * Property filters
   */
  properties?: Record<string, any>;

  /**
   * Context filters
   */
  context?: Record<string, any>;

  /**
   * Start timestamp
   */
  startTime?: Date;

  /**
   * End timestamp
   */
  endTime?: Date;

  /**
   * Maximum results to return
   */
  limit?: number;

  /**
   * Result offset for pagination
   */
  offset?: number;

  /**
   * Sort field
   */
  sortBy?: string;

  /**
   * Sort direction
   */
  sortDirection?: 'asc' | 'desc';
}

/**
 * Analytics query result
 */
export interface AnalyticsQueryResult {
  /**
   * Matching events
   */
  events: AnalyticsEvent[];

  /**
   * Total count of matching events
   */
  totalCount: number;

  /**
   * Page size
   */
  limit: number;

  /**
   * Result offset
   */
  offset: number;
}

/**
 * Timeframe for analytics queries
 */
export interface TimeFrame {
  /**
   * Start date
   */
  start: Date;

  /**
   * End date
   */
  end: Date;
}

/**
 * Aggregated metrics result
 */
export interface AggregatedMetrics {
  /**
   * Metric name
   */
  metric: string;

  /**
   * Dimensions used for grouping
   */
  dimensions: string[];

  /**
   * Grouped results
   */
  groups: Array<{
    /**
     * Dimension values
     */
    dimensions: Record<string, any>;

    /**
     * Aggregate value
     */
    value: number;
  }>;

  /**
   * Overall total
   */
  total: number;
}

/**
 * Analytics service configuration
 */
export interface AnalyticsServiceConfig {
  /**
   * Storage provider
   */
  storageProvider: AnalyticsStorageProvider;

  /**
   * Whether to validate events
   */
  validateEvents?: boolean;

  /**
   * Whether to batch events for storage
   */
  batchEvents?: boolean;

  /**
   * Batch size when batching is enabled
   */
  batchSize?: number;

  /**
   * Batch flush interval in milliseconds
   */
  batchFlushIntervalMs?: number;

  /**
   * Whether to enable real-time processing
   */
  realtime?: boolean;

  /**
   * Number of worker threads for processing
   */
  workers?: number;
}

/**
 * Analytics service
 */
export class AnalyticsService {
  private storageProvider: AnalyticsStorageProvider;
  private validateEvents: boolean;
  private batchEvents: boolean;
  private batchSize: number;
  private batchFlushIntervalMs: number;
  private realtime: boolean;
  private workers: number;

  private eventBatch: AnalyticsEvent[] = [];
  private flushInterval: NodeJS.Timeout | null = null;
  private eventEmitter = new EventEmitter();
  private processing = false;

  /**
   * Create an analytics service
   * @param config Service configuration
   */
  constructor(config: AnalyticsServiceConfig) {
    this.storageProvider = config.storageProvider;
    this.validateEvents = config.validateEvents ?? true;
    this.batchEvents = config.batchEvents ?? true;
    this.batchSize = config.batchSize ?? 100;
    this.batchFlushIntervalMs = config.batchFlushIntervalMs ?? 5000;
    this.realtime = config.realtime ?? false;
    this.workers = config.workers ?? 1;

    if (this.batchEvents) {
      this.flushInterval = setInterval(() => this.flushBatch(), this.batchFlushIntervalMs);
    }

    // Set up real-time processing
    if (this.realtime) {
      this.eventEmitter.on('event', this.processRealtimeEvent.bind(this));
    }
  }

  /**
   * Track an analytics event
   * @param event Analytics event to track
   * @returns Promise resolving to the tracked event
   */
  async trackEvent(event: Partial<AnalyticsEvent>): Promise<AnalyticsEvent> {
    // Generate missing fields
    const fullEvent: AnalyticsEvent = {
      id: event.id ?? uuidv4(),
      type: event.type ?? 'custom',
      name: event.name ?? 'custom_event',
      timestamp: event.timestamp ?? new Date(),
      userId: event.userId,
      sessionId: event.sessionId,
      properties: event.properties,
      context: event.context,
      source: event.source ?? 'analytics-service',
    };

    // Validate the event if enabled
    if (this.validateEvents) {
      this.validateEvent(fullEvent);
    }

    // Batch or immediately store the event
    if (this.batchEvents) {
      this.eventBatch.push(fullEvent);

      // Flush if batch is full
      if (this.eventBatch.length >= this.batchSize) {
        this.flushBatch();
      }
    } else {
      await this.storageProvider.storeEvent(fullEvent);
    }

    // Emit for real-time processing
    this.eventEmitter.emit('event', fullEvent);

    return fullEvent;
  }

  /**
   * Query analytics events
   * @param query Query parameters
   * @returns Promise resolving to query results
   */
  async queryEvents(query: AnalyticsQuery): Promise<AnalyticsQueryResult> {
    return this.storageProvider.queryEvents(query);
  }

  /**
   * Get aggregated metrics
   * @param metric Metric to aggregate
   * @param dimensions Dimensions to group by
   * @param filters Filters to apply
   * @param timeframe Timeframe to query
   * @returns Promise resolving to aggregated metrics
   */
  async getMetrics(
    metric: string,
    dimensions: string[] = [],
    filters: Record<string, any> = {},
    timeframe: TimeFrame = { start: new Date(Date.now() - 86400000), end: new Date() }
  ): Promise<AggregatedMetrics> {
    return this.storageProvider.getMetrics(metric, dimensions, filters, timeframe);
  }

  /**
   * Subscribe to real-time events
   * @param callback Callback function for events
   * @returns Unsubscribe function
   */
  subscribeToEvents(callback: (event: AnalyticsEvent) => void): () => void {
    this.eventEmitter.on('event', callback);

    return () => {
      this.eventEmitter.off('event', callback);
    };
  }

  /**
   * Validate an analytics event
   * @param event Event to validate
   */
  private validateEvent(event: AnalyticsEvent): void {
    // Perform basic validation
    if (!event.type) {
      throw new Error('Event must have a type');
    }

    if (!event.name) {
      throw new Error('Event must have a name');
    }

    if (!event.timestamp) {
      throw new Error('Event must have a timestamp');
    }
  }

  /**
   * Process a real-time event
   * @param event Event to process
   */
  private processRealtimeEvent(event: AnalyticsEvent): void {
    // Implement real-time processing logic here
    // This could include:
    // - Triggering alerts
    // - Updating real-time dashboards
    // - Implementing real-time fraud detection
    // - etc.

    logger.debug(`Processing real-time event: ${event.type}:${event.name}`);
  }

  /**
   * Flush the current batch of events
   */
  private async flushBatch(): Promise<void> {
    if (this.eventBatch.length === 0 || this.processing) {
      return;
    }

    this.processing = true;
    const batchToProcess = [...this.eventBatch];
    this.eventBatch = [];

    try {
      // Process events in batches to avoid memory issues
      const batchSize = 100;
      for (let i = 0; i < batchToProcess.length; i += batchSize) {
        const batch = batchToProcess.slice(i, i + batchSize);

        // Store each event in the batch
        await Promise.all(batch.map(event => this.storageProvider.storeEvent(event)));
      }

      logger.debug(`Flushed ${batchToProcess.length} events to storage`);
    } catch (error) {
      logger.error('Error flushing event batch', { error });

      // Put events back in the batch to retry
      this.eventBatch = [...batchToProcess, ...this.eventBatch];
    } finally {
      this.processing = false;
    }
  }

  /**
   * Clean up resources
   */
  async shutdown(): Promise<void> {
    // Clear the flush interval
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }

    // Flush any remaining events
    await this.flushBatch();

    // Remove all event listeners
    this.eventEmitter.removeAllListeners();
  }
}

/**
 * Create a default time frame for the last N days
 * @param days Number of days
 * @returns Time frame
 */
export function createTimeFrame(days: number): TimeFrame {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);

  return { start, end };
}

/**
 * Create predefined time frames
 */
export const TimeFrames = {
  /**
   * Last 24 hours
   */
  LAST_24_HOURS: createTimeFrame(1),

  /**
   * Last 7 days
   */
  LAST_7_DAYS: createTimeFrame(7),

  /**
   * Last 30 days
   */
  LAST_30_DAYS: createTimeFrame(30),

  /**
   * Last 90 days
   */
  LAST_90_DAYS: createTimeFrame(90),

  /**
   * Custom time frame
   * @param start Start date
   * @param end End date
   * @returns Time frame
   */
  custom(start: Date, end: Date): TimeFrame {
    return { start, end };
  },
};

export default AnalyticsService;
