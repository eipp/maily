import { Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import logger from '../utils/logger';
import eventProcessor from '../processors/event-processor';
import Event from '../models/event.model';
import { RabbitMQPublisher } from '../events/rabbitmq';
import { getCache, setCache } from '../utils/cache';
import { EventMessage } from '../events/interfaces';

// Create RabbitMQ publisher instance
const eventPublisher = new RabbitMQPublisher();

/**
 * Controller for handling events
 */
export default {
  /**
   * Track a new event
   * @route POST /api/v1/events
   */
  async trackEvent(req: Request, res: Response): Promise<void> {
    try {
      const { type, data, source, timestamp, correlationId, metadata } = req.body;

      if (!type || !data) {
        res.status(400).json({
          success: false,
          message: 'Event type and data are required',
        });
        return;
      }

      const eventId = uuidv4();
      const eventTimestamp = timestamp ? new Date(timestamp) : new Date();

      // Create event message
      const event: EventMessage = {
        id: eventId,
        type,
        data,
        timestamp: eventTimestamp,
        source: source || 'api',
        correlationId: correlationId || eventId,
        metadata: metadata || {},
      };

      // Process event asynchronously
      setImmediate(async () => {
        try {
          // Initialize publisher if not already initialized
          if (!eventPublisher.publish) {
            await eventPublisher.initialize();
          }

          // Publish event to message broker
          await eventPublisher.publish(event);

          // Process event directly
          await eventProcessor.processEvent(event);
        } catch (error: any) {
          logger.error('Error processing tracked event', {
            eventId,
            eventType: type,
            error: error.message,
          });
        }
      });

      // Respond immediately
      res.status(202).json({
        success: true,
        message: 'Event accepted for processing',
        eventId,
      });
    } catch (error: any) {
      logger.error('Error tracking event', { error: error.message });
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  },

  /**
   * Track multiple events in batch
   * @route POST /api/v1/events/batch
   */
  async trackBatchEvents(req: Request, res: Response): Promise<void> {
    try {
      const { events } = req.body;

      if (!Array.isArray(events) || events.length === 0) {
        res.status(400).json({
          success: false,
          message: 'Events array is required and must not be empty',
        });
        return;
      }

      const processedEvents: EventMessage[] = [];

      // Process each event in the batch
      for (const eventData of events) {
        const { type, data, source, timestamp, correlationId, metadata } = eventData;

        if (!type || !data) {
          continue; // Skip invalid events
        }

        const eventId = uuidv4();
        const eventTimestamp = timestamp ? new Date(timestamp) : new Date();

        // Create event message
        const event: EventMessage = {
          id: eventId,
          type,
          data,
          timestamp: eventTimestamp,
          source: source || 'api',
          correlationId: correlationId || eventId,
          metadata: metadata || {},
        };

        processedEvents.push(event);
      }

      // Process events asynchronously
      setImmediate(async () => {
        try {
          // Initialize publisher if not already initialized
          if (!eventPublisher.publish) {
            await eventPublisher.initialize();
          }

          // Publish events to message broker
          await eventPublisher.publishBatch(processedEvents);

          // Process events directly
          await eventProcessor.processBatch(processedEvents);
        } catch (error: any) {
          logger.error('Error processing batch events', {
            count: processedEvents.length,
            error: error.message,
          });
        }
      });

      // Respond immediately
      res.status(202).json({
        success: true,
        message: 'Batch events accepted for processing',
        count: processedEvents.length,
        eventIds: processedEvents.map(event => event.id),
      });
    } catch (error: any) {
      logger.error('Error tracking batch events', { error: error.message });
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  },

  /**
   * Get events with filtering options
   * @route GET /api/v1/events
   */
  async getEvents(req: Request, res: Response): Promise<void> {
    try {
      const {
        type,
        source,
        startDate,
        endDate,
        userId,
        sessionId,
        page = 1,
        limit = 50,
        sort = '-timestamp',
      } = req.query;

      // Build query filters
      const filter: any = {};

      if (type) {
        filter.eventType = type;
      }

      if (source) {
        filter.source = source;
      }

      if (userId) {
        filter.userId = userId;
      }

      if (sessionId) {
        filter.sessionId = sessionId;
      }

      // Date range filter
      if (startDate || endDate) {
        filter.timestamp = {};

        if (startDate) {
          filter.timestamp.$gte = new Date(startDate as string);
        }

        if (endDate) {
          filter.timestamp.$lte = new Date(endDate as string);
        }
      }

      // Check cache for this query
      const cacheKey = `events:${JSON.stringify({
        filter,
        page,
        limit,
        sort,
      })}`;

      const cachedResult = await getCache(cacheKey);

      if (cachedResult) {
        res.status(200).json(cachedResult);
        return;
      }

      // Calculate pagination
      const skip = (Number(page) - 1) * Number(limit);

      // Execute query
      const events = await Event.find(filter)
        .sort(sort)
        .skip(skip)
        .limit(Number(limit));

      // Get total count
      const total = await Event.countDocuments(filter);

      // Prepare response
      const result = {
        success: true,
        data: events,
        pagination: {
          total,
          page: Number(page),
          limit: Number(limit),
          pages: Math.ceil(total / Number(limit)),
        },
      };

      // Cache result
      await setCache(cacheKey, result, 300); // Cache for 5 minutes

      res.status(200).json(result);
    } catch (error: any) {
      logger.error('Error getting events', { error: error.message });
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  },

  /**
   * Get a specific event by ID
   * @route GET /api/v1/events/:id
   */
  async getEventById(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      // Check cache first
      const cacheKey = `event:${id}`;
      const cachedEvent = await getCache(cacheKey);

      if (cachedEvent) {
        res.status(200).json({
          success: true,
          data: cachedEvent,
        });
        return;
      }

      // Find event by ID
      const event = await Event.findOne({ eventId: id });

      if (!event) {
        res.status(404).json({
          success: false,
          message: 'Event not found',
        });
        return;
      }

      // Cache event
      await setCache(cacheKey, event, 3600); // Cache for 1 hour

      res.status(200).json({
        success: true,
        data: event,
      });
    } catch (error: any) {
      logger.error('Error getting event by ID', {
        eventId: req.params.id,
        error: error.message,
      });
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  },

  /**
   * Get event counts by type
   * @route GET /api/v1/events/counts
   */
  async getEventCounts(req: Request, res: Response): Promise<void> {
    try {
      const { startDate, endDate, source } = req.query;

      // Build time range filter
      const timeFilter: any = {};

      if (startDate) {
        timeFilter.$gte = new Date(startDate as string);
      }

      if (endDate) {
        timeFilter.$lte = new Date(endDate as string);
      }

      // Check cache for this query
      const cacheKey = `event-counts:${JSON.stringify({
        timeFilter,
        source,
      })}`;

      const cachedCounts = await getCache(cacheKey);

      if (cachedCounts) {
        res.status(200).json({
          success: true,
          data: cachedCounts,
        });
        return;
      }

      // Build aggregation pipeline
      const pipeline: any[] = [
        {
          $match: {
            ...(Object.keys(timeFilter).length > 0 ? { timestamp: timeFilter } : {}),
            ...(source ? { source } : {}),
          },
        },
        {
          $group: {
            _id: '$eventType',
            count: { $sum: 1 },
          },
        },
        {
          $sort: { count: -1 },
        },
      ];

      // Execute aggregation
      const counts = await Event.aggregate(pipeline);

      // Format result
      const formattedCounts = counts.map(item => ({
        type: item._id,
        count: item.count,
      }));

      // Cache result
      await setCache(cacheKey, formattedCounts, 300); // Cache for 5 minutes

      res.status(200).json({
        success: true,
        data: formattedCounts,
      });
    } catch (error: any) {
      logger.error('Error getting event counts', { error: error.message });
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  },
};
