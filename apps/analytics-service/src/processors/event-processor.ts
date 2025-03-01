import { v4 as uuidv4 } from 'uuid';
import logger from '../utils/logger';
import { EventMessage } from '../events/interfaces';
import Event, { EventDocument } from '../models/event.model';
import Session from '../models/session.model';
import Metric, { MetricType, TimeGranularity } from '../models/metric.model';
import { setCache, getCache } from '../utils/cache';

/**
 * Analytics event processor
 * Processes incoming events and stores them in the database
 */
export class EventProcessor {
  /**
   * Process a single analytics event
   * @param event The event to process
   * @returns The processed event document
   */
  async processEvent(event: EventMessage): Promise<EventDocument> {
    try {
      const startTime = Date.now();

      // Create event document
      const eventDoc = new Event({
        eventId: event.id,
        eventType: event.type,
        timestamp: event.timestamp,
        source: event.source,
        userId: event.data.userId,
        sessionId: event.data.sessionId,
        ip: event.data.ip,
        userAgent: event.data.userAgent,
        properties: event.data,
        metadata: event.metadata || {},
      });

      // Save event to database
      await eventDoc.save();

      // Update session if session ID is provided
      if (event.data.sessionId) {
        await this.updateSession(event);
      }

      // Update metrics
      await this.updateMetrics(event);

      // Calculate processing time
      const processingTime = Date.now() - startTime;
      eventDoc.processingTime = processingTime;
      await eventDoc.save();

      logger.info('Event processed successfully', {
        eventId: event.id,
        eventType: event.type,
        processingTime,
      });

      return eventDoc;
    } catch (error: any) {
      logger.error('Error processing event', {
        eventId: event.id,
        eventType: event.type,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Process multiple events in batch
   * @param events The events to process
   * @returns The processed event documents
   */
  async processBatch(events: EventMessage[]): Promise<EventDocument[]> {
    if (events.length === 0) return [];

    logger.info(`Processing batch of ${events.length} events`);

    try {
      const processedEvents: EventDocument[] = [];

      // Process each event sequentially
      // In a production environment, this could be optimized with bulk operations
      for (const event of events) {
        const processedEvent = await this.processEvent(event);
        processedEvents.push(processedEvent);
      }

      return processedEvents;
    } catch (error: any) {
      logger.error('Error processing event batch', {
        count: events.length,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Update session data based on the event
   * @param event The event containing session data
   */
  private async updateSession(event: EventMessage): Promise<void> {
    if (!event.data.sessionId) return;

    try {
      const sessionId = event.data.sessionId;
      const cacheKey = `session:${sessionId}`;

      // Try to get session from cache first
      let session = await getCache<any>(cacheKey);

      if (!session) {
        // Find or create session in database
        session = await Session.findOne({ sessionId });

        if (!session) {
          // Create new session
          session = new Session({
            sessionId,
            userId: event.data.userId,
            startTime: event.timestamp,
            ip: event.data.ip,
            userAgent: event.data.userAgent,
            device: this.extractDevice(event.data.userAgent),
            browser: this.extractBrowser(event.data.userAgent),
            os: this.extractOS(event.data.userAgent),
            country: event.data.country,
            region: event.data.region,
            city: event.data.city,
            referrer: event.data.referrer,
            entryPage: event.data.page,
            pageViews: 0,
            events: 0,
            bounced: true,
          });
        }
      }

      // Update session data
      session.endTime = event.timestamp;

      // Calculate duration in seconds
      if (session.startTime) {
        const durationMs = new Date(event.timestamp).getTime() - new Date(session.startTime).getTime();
        session.duration = Math.round(durationMs / 1000);
      }

      // Increment event count
      session.events = (session.events || 0) + 1;

      // Update page views if this is a page view event
      if (event.type === 'page_view') {
        session.pageViews = (session.pageViews || 0) + 1;

        // If this is the second page view, the session is no longer bounced
        if (session.pageViews >= 2) {
          session.bounced = false;
        }

        // Update exit page
        session.exitPage = event.data.page;
      }

      // Save to database and cache
      await session.save();
      await setCache(cacheKey, session, 3600); // Cache for 1 hour

      logger.debug('Session updated successfully', {
        sessionId,
        pageViews: session.pageViews,
        events: session.events,
      });
    } catch (error: any) {
      logger.error('Error updating session', {
        sessionId: event.data.sessionId,
        error: error.message,
      });
    }
  }

  /**
   * Update metrics based on the event
   * @param event The event to update metrics for
   */
  private async updateMetrics(event: EventMessage): Promise<void> {
    try {
      // Get timestamp for today at midnight
      const today = new Date(event.timestamp);
      today.setHours(0, 0, 0, 0);

      // Get timestamp for the start of the hour
      const hourStart = new Date(event.timestamp);
      hourStart.setMinutes(0, 0, 0);

      // Update daily event count metric
      await this.updateCountMetric(
        `events.${event.type}.daily`,
        today,
        new Date(today.getTime() + 24 * 60 * 60 * 1000),
        TimeGranularity.DAY,
        { source: event.source }
      );

      // Update hourly event count metric
      await this.updateCountMetric(
        `events.${event.type}.hourly`,
        hourStart,
        new Date(hourStart.getTime() + 60 * 60 * 1000),
        TimeGranularity.HOUR,
        { source: event.source }
      );

      // Update user count metric if user ID is present
      if (event.data.userId) {
        await this.updateUniqueMetric(
          'users.active.daily',
          event.data.userId,
          today,
          new Date(today.getTime() + 24 * 60 * 60 * 1000),
          TimeGranularity.DAY
        );
      }

      // Update session count metric if session ID is present
      if (event.data.sessionId) {
        await this.updateUniqueMetric(
          'sessions.daily',
          event.data.sessionId,
          today,
          new Date(today.getTime() + 24 * 60 * 60 * 1000),
          TimeGranularity.DAY
        );
      }

      // Process event-specific metrics
      switch (event.type) {
        case 'page_view':
          await this.processPageViewMetrics(event, today, hourStart);
          break;

        case 'user_signup':
          await this.updateCountMetric(
            'users.signup.daily',
            today,
            new Date(today.getTime() + 24 * 60 * 60 * 1000),
            TimeGranularity.DAY
          );
          break;

        case 'error':
          await this.updateCountMetric(
            'errors.daily',
            today,
            new Date(today.getTime() + 24 * 60 * 60 * 1000),
            TimeGranularity.DAY,
            { type: event.data.errorType || 'unknown' }
          );
          break;
      }

    } catch (error: any) {
      logger.error('Error updating metrics', {
        eventId: event.id,
        eventType: event.type,
        error: error.message,
      });
    }
  }

  /**
   * Process page view specific metrics
   * @param event The page view event
   * @param today Timestamp for today at midnight
   * @param hourStart Timestamp for the start of the hour
   */
  private async processPageViewMetrics(
    event: EventMessage,
    today: Date,
    hourStart: Date
  ): Promise<void> {
    try {
      // Update daily page view count
      await this.updateCountMetric(
        'page_views.daily',
        today,
        new Date(today.getTime() + 24 * 60 * 60 * 1000),
        TimeGranularity.DAY,
        { page: event.data.page }
      );

      // Update hourly page view count
      await this.updateCountMetric(
        'page_views.hourly',
        hourStart,
        new Date(hourStart.getTime() + 60 * 60 * 1000),
        TimeGranularity.HOUR,
        { page: event.data.page }
      );

      // Update page performance metrics if available
      if (event.data.performance && typeof event.data.performance === 'object') {
        const { loadTime, ttfb, fcp, lcp, cls } = event.data.performance;

        if (typeof loadTime === 'number') {
          await this.updateAverageMetric(
            'performance.load_time.daily',
            loadTime,
            today,
            new Date(today.getTime() + 24 * 60 * 60 * 1000),
            TimeGranularity.DAY,
            { page: event.data.page }
          );
        }

        if (typeof ttfb === 'number') {
          await this.updateAverageMetric(
            'performance.ttfb.daily',
            ttfb,
            today,
            new Date(today.getTime() + 24 * 60 * 60 * 1000),
            TimeGranularity.DAY,
            { page: event.data.page }
          );
        }
      }
    } catch (error: any) {
      logger.error('Error processing page view metrics', {
        eventId: event.id,
        error: error.message,
      });
    }
  }

  /**
   * Update a count metric
   * @param name Metric name
   * @param startPeriod Start of the period
   * @param endPeriod End of the period
   * @param timeGranularity Time granularity
   * @param dimensions Optional dimensions
   */
  private async updateCountMetric(
    name: string,
    startPeriod: Date,
    endPeriod: Date,
    timeGranularity: TimeGranularity,
    dimensions: Record<string, string | number> = {}
  ): Promise<void> {
    try {
      // Find or create metric
      const metric = await Metric.findOneAndUpdate(
        {
          name,
          type: MetricType.COUNT,
          timeGranularity,
          startPeriod,
          endPeriod,
          dimensions,
        },
        {
          $inc: { value: 1 },
          $setOnInsert: {
            timestamp: new Date(),
          },
        },
        {
          upsert: true,
          new: true,
        }
      );

      logger.debug('Count metric updated', {
        name,
        value: metric.value,
        timeGranularity,
      });
    } catch (error: any) {
      logger.error('Error updating count metric', {
        name,
        timeGranularity,
        error: error.message,
      });
    }
  }

  /**
   * Update a unique items metric
   * @param name Metric name
   * @param itemId Unique item ID
   * @param startPeriod Start of the period
   * @param endPeriod End of the period
   * @param timeGranularity Time granularity
   * @param dimensions Optional dimensions
   */
  private async updateUniqueMetric(
    name: string,
    itemId: string,
    startPeriod: Date,
    endPeriod: Date,
    timeGranularity: TimeGranularity,
    dimensions: Record<string, string | number> = {}
  ): Promise<void> {
    try {
      // Cache key for unique items set
      const cacheKey = `metric:${name}:${timeGranularity}:${startPeriod.toISOString()}:${JSON.stringify(dimensions)}`;

      // Find or create metric
      const metric = await Metric.findOne({
        name,
        type: MetricType.UNIQUE,
        timeGranularity,
        startPeriod,
        endPeriod,
        dimensions,
      });

      if (metric) {
        // Check if item is already counted
        const items = metric.value as Record<string, number>;

        if (!items[itemId]) {
          // Add new item
          items[itemId] = 1;
          metric.value = items;
          await metric.save();
        }
      } else {
        // Create new metric with the first item
        const newMetric = new Metric({
          name,
          type: MetricType.UNIQUE,
          value: { [itemId]: 1 },
          dimensions,
          timestamp: new Date(),
          timeGranularity,
          startPeriod,
          endPeriod,
        });

        await newMetric.save();
      }

      logger.debug('Unique metric updated', {
        name,
        itemId,
        timeGranularity,
      });
    } catch (error: any) {
      logger.error('Error updating unique metric', {
        name,
        timeGranularity,
        error: error.message,
      });
    }
  }

  /**
   * Update an average metric
   * @param name Metric name
   * @param value New value to include in average
   * @param startPeriod Start of the period
   * @param endPeriod End of the period
   * @param timeGranularity Time granularity
   * @param dimensions Optional dimensions
   */
  private async updateAverageMetric(
    name: string,
    value: number,
    startPeriod: Date,
    endPeriod: Date,
    timeGranularity: TimeGranularity,
    dimensions: Record<string, string | number> = {}
  ): Promise<void> {
    try {
      // Find existing metric
      const existingMetric = await Metric.findOne({
        name,
        type: MetricType.AVERAGE,
        timeGranularity,
        startPeriod,
        endPeriod,
        dimensions,
      });

      if (existingMetric) {
        // Update average
        const data = existingMetric.value as Record<string, number>;
        const count = (data.count || 0) + 1;
        const sum = (data.sum || 0) + value;
        const average = sum / count;

        existingMetric.value = {
          average,
          sum,
          count,
          min: Math.min(data.min || value, value),
          max: Math.max(data.max || value, value),
        };

        await existingMetric.save();
      } else {
        // Create new metric
        const newMetric = new Metric({
          name,
          type: MetricType.AVERAGE,
          value: {
            average: value,
            sum: value,
            count: 1,
            min: value,
            max: value,
          },
          dimensions,
          timestamp: new Date(),
          timeGranularity,
          startPeriod,
          endPeriod,
        });

        await newMetric.save();
      }

      logger.debug('Average metric updated', {
        name,
        value,
        timeGranularity,
      });
    } catch (error: any) {
      logger.error('Error updating average metric', {
        name,
        timeGranularity,
        error: error.message,
      });
    }
  }

  /**
   * Extract device type from user agent
   * @param userAgent User agent string
   * @returns Device type
   */
  private extractDevice(userAgent?: string): string {
    if (!userAgent) return 'unknown';

    const ua = userAgent.toLowerCase();

    if (/ipad|tablet|playbook|silk/i.test(ua)) {
      return 'tablet';
    }

    if (/mobile|iphone|android|webos|blackberry|windows phone/i.test(ua)) {
      return 'mobile';
    }

    return 'desktop';
  }

  /**
   * Extract browser from user agent
   * @param userAgent User agent string
   * @returns Browser name
   */
  private extractBrowser(userAgent?: string): string {
    if (!userAgent) return 'unknown';

    const ua = userAgent.toLowerCase();

    if (ua.includes('firefox') && !ua.includes('seamonkey')) {
      return 'firefox';
    } else if (ua.includes('seamonkey')) {
      return 'seamonkey';
    } else if (ua.includes('chrome') && !ua.includes('chromium') && !ua.includes('edg')) {
      return 'chrome';
    } else if (ua.includes('chromium')) {
      return 'chromium';
    } else if (ua.includes('safari') && !ua.includes('chrome') && !ua.includes('chromium')) {
      return 'safari';
    } else if (ua.includes('edg')) {
      return 'edge';
    } else if (ua.includes('opera') || ua.includes('opr')) {
      return 'opera';
    } else if (ua.includes('msie') || ua.includes('trident')) {
      return 'ie';
    }

    return 'unknown';
  }

  /**
   * Extract operating system from user agent
   * @param userAgent User agent string
   * @returns Operating system name
   */
  private extractOS(userAgent?: string): string {
    if (!userAgent) return 'unknown';

    const ua = userAgent.toLowerCase();

    if (ua.includes('windows nt 10')) {
      return 'windows 10';
    } else if (ua.includes('windows nt 6.3')) {
      return 'windows 8.1';
    } else if (ua.includes('windows nt 6.2')) {
      return 'windows 8';
    } else if (ua.includes('windows nt 6.1')) {
      return 'windows 7';
    } else if (ua.includes('windows')) {
      return 'windows';
    } else if (ua.includes('mac os x')) {
      return 'macos';
    } else if (ua.includes('android')) {
      return 'android';
    } else if (ua.includes('ios') || ua.includes('iphone') || ua.includes('ipad')) {
      return 'ios';
    } else if (ua.includes('linux')) {
      return 'linux';
    }

    return 'unknown';
  }
}

// Export singleton instance
export default new EventProcessor();
