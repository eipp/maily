import amqp, { Connection, Channel, ConsumeMessage } from 'amqplib';
import logger from '../utils/logger';
import config from '../config';
import { EventMessage, EventPublisher, EventSubscriber, EventHandler, BrokerOptions } from './interfaces';

/**
 * RabbitMQ event publisher implementation
 */
export class RabbitMQPublisher implements EventPublisher {
  private connection: Connection | null = null;
  private channel: Channel | null = null;
  private options: BrokerOptions;

  /**
   * Create a new RabbitMQ publisher
   * @param options RabbitMQ connection options
   */
  constructor(options?: Partial<BrokerOptions>) {
    this.options = {
      url: options?.url ?? config.rabbitmq.url,
      exchange: options?.exchange ?? config.rabbitmq.exchange,
      queue: options?.queue ?? config.rabbitmq.queue,
      connectionTimeout: options?.connectionTimeout ?? 30000,
      autoReconnect: options?.autoReconnect ?? true,
    };
  }

  /**
   * Initialize the RabbitMQ connection and channel
   */
  async initialize(): Promise<void> {
    try {
      // Connect to RabbitMQ
      this.connection = await amqp.connect(this.options.url);

      // Create a channel
      this.channel = await this.connection.createChannel();

      // Assert exchange exists
      await this.channel.assertExchange(this.options.exchange, 'topic', {
        durable: true,
      });

      logger.info('RabbitMQ publisher initialized successfully');

      // Handle connection errors
      this.connection.on('error', (err) => {
        logger.error('RabbitMQ connection error', { error: err.message });
        this.reconnect();
      });

      // Handle connection close
      this.connection.on('close', () => {
        logger.warn('RabbitMQ connection closed');
        if (this.options.autoReconnect) {
          this.reconnect();
        }
      });
    } catch (error: any) {
      logger.error('Failed to initialize RabbitMQ publisher', { error: error.message });
      throw error;
    }
  }

  /**
   * Publish an event to RabbitMQ
   * @param event The event to publish
   */
  async publish(event: EventMessage): Promise<void> {
    if (!this.channel) {
      throw new Error('RabbitMQ publisher not initialized');
    }

    try {
      // Create routing key from event type
      const routingKey = event.type.replace(/\./g, '-');

      // Publish the event
      this.channel.publish(
        this.options.exchange,
        routingKey,
        Buffer.from(JSON.stringify(event)),
        {
          persistent: true,
          contentType: 'application/json',
          contentEncoding: 'utf-8',
          messageId: event.id,
          timestamp: event.timestamp.getTime(),
          appId: 'analytics-service',
          headers: {
            'x-event-source': event.source,
            'x-correlation-id': event.correlationId || event.id,
            ...event.metadata,
          },
        }
      );
    } catch (error: any) {
      logger.error('Error publishing event to RabbitMQ', {
        eventId: event.id,
        eventType: event.type,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Publish multiple events to RabbitMQ
   * @param events The events to publish
   */
  async publishBatch(events: EventMessage[]): Promise<void> {
    if (events.length === 0) return;

    try {
      // Publish each event sequentially
      for (const event of events) {
        await this.publish(event);
      }
    } catch (error: any) {
      logger.error('Error batch publishing events to RabbitMQ', {
        count: events.length,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Close the RabbitMQ connection
   */
  async close(): Promise<void> {
    try {
      if (this.channel) {
        await this.channel.close();
        this.channel = null;
      }

      if (this.connection) {
        await this.connection.close();
        this.connection = null;
      }

      logger.info('RabbitMQ publisher closed');
    } catch (error: any) {
      logger.error('Error closing RabbitMQ publisher', { error: error.message });
      throw error;
    }
  }

  /**
   * Reconnect to RabbitMQ after a connection failure
   */
  private async reconnect(): Promise<void> {
    if (!this.options.autoReconnect) return;

    // Reset connection and channel
    this.connection = null;
    this.channel = null;

    let retryCount = 0;
    const maxRetries = 10;
    const initialDelay = 1000;

    const attemptReconnect = async (): Promise<void> => {
      try {
        logger.info(`Attempting to reconnect to RabbitMQ (attempt ${retryCount + 1}/${maxRetries})...`);
        await this.initialize();
        logger.info('Successfully reconnected to RabbitMQ');
      } catch (error: any) {
        retryCount++;

        if (retryCount >= maxRetries) {
          logger.error('Failed to reconnect to RabbitMQ after maximum retries', {
            error: error.message,
          });
          return;
        }

        const delay = initialDelay * Math.pow(2, retryCount);
        logger.info(`Retrying RabbitMQ connection in ${delay}ms...`);

        setTimeout(attemptReconnect, delay);
      }
    };

    // Start reconnection process
    setTimeout(attemptReconnect, initialDelay);
  }
}

/**
 * RabbitMQ event subscriber implementation
 */
export class RabbitMQSubscriber implements EventSubscriber {
  private connection: Connection | null = null;
  private channel: Channel | null = null;
  private options: BrokerOptions;
  private handlers: Map<string, EventHandler> = new Map();
  private consumerTags: Map<string, string> = new Map();

  /**
   * Create a new RabbitMQ subscriber
   * @param options RabbitMQ connection options
   */
  constructor(options?: Partial<BrokerOptions>) {
    this.options = {
      url: options?.url ?? config.rabbitmq.url,
      exchange: options?.exchange ?? config.rabbitmq.exchange,
      queue: options?.queue ?? config.rabbitmq.queue,
      connectionTimeout: options?.connectionTimeout ?? 30000,
      autoReconnect: options?.autoReconnect ?? true,
    };
  }

  /**
   * Initialize the RabbitMQ connection and channel
   */
  async initialize(): Promise<void> {
    try {
      // Connect to RabbitMQ
      this.connection = await amqp.connect(this.options.url);

      // Create a channel
      this.channel = await this.connection.createChannel();

      // Assert exchange exists
      await this.channel.assertExchange(this.options.exchange, 'topic', {
        durable: true,
      });

      // Assert queue exists
      await this.channel.assertQueue(this.options.queue, {
        durable: true,
        arguments: {
          'x-message-ttl': 86400000, // 24 hours
          'x-dead-letter-exchange': `${this.options.exchange}.dlx`,
        },
      });

      logger.info('RabbitMQ subscriber initialized successfully');

      // Handle connection errors
      this.connection.on('error', (err) => {
        logger.error('RabbitMQ connection error', { error: err.message });
        this.reconnect();
      });

      // Handle connection close
      this.connection.on('close', () => {
        logger.warn('RabbitMQ connection closed');
        if (this.options.autoReconnect) {
          this.reconnect();
        }
      });

      // Resubscribe to event types if we have handlers
      if (this.handlers.size > 0) {
        for (const [eventType] of this.handlers) {
          await this.subscribeToEventType(eventType);
        }
      }
    } catch (error: any) {
      logger.error('Failed to initialize RabbitMQ subscriber', { error: error.message });
      throw error;
    }
  }

  /**
   * Subscribe to an event type
   * @param eventType The event type to subscribe to
   * @param handler The handler function for events
   */
  async subscribe(eventType: string, handler: EventHandler): Promise<void> {
    if (!this.channel) {
      throw new Error('RabbitMQ subscriber not initialized');
    }

    try {
      // Store the handler
      this.handlers.set(eventType, handler);

      // Subscribe to the event type
      await this.subscribeToEventType(eventType);

      logger.info(`Subscribed to event type: ${eventType}`);
    } catch (error: any) {
      logger.error('Error subscribing to event type', { eventType, error: error.message });
      throw error;
    }
  }

  /**
   * Subscribe to multiple event types
   * @param eventTypes The event types to subscribe to
   * @param handler The handler function for events
   */
  async subscribeMultiple(eventTypes: string[], handler: EventHandler): Promise<void> {
    for (const eventType of eventTypes) {
      await this.subscribe(eventType, handler);
    }
  }

  /**
   * Unsubscribe from an event type
   * @param eventType The event type to unsubscribe from
   */
  async unsubscribe(eventType: string): Promise<void> {
    if (!this.channel) {
      throw new Error('RabbitMQ subscriber not initialized');
    }

    try {
      // Get the consumer tag
      const consumerTag = this.consumerTags.get(eventType);

      if (consumerTag) {
        // Cancel the consumer
        await this.channel.cancel(consumerTag);

        // Remove the binding
        const routingKey = eventType.replace(/\./g, '-');
        await this.channel.unbindQueue(this.options.queue, this.options.exchange, routingKey);

        // Remove the handler and tag
        this.handlers.delete(eventType);
        this.consumerTags.delete(eventType);

        logger.info(`Unsubscribed from event type: ${eventType}`);
      }
    } catch (error: any) {
      logger.error('Error unsubscribing from event type', { eventType, error: error.message });
      throw error;
    }
  }

  /**
   * Close the RabbitMQ connection
   */
  async close(): Promise<void> {
    try {
      if (this.channel) {
        await this.channel.close();
        this.channel = null;
      }

      if (this.connection) {
        await this.connection.close();
        this.connection = null;
      }

      logger.info('RabbitMQ subscriber closed');
    } catch (error: any) {
      logger.error('Error closing RabbitMQ subscriber', { error: error.message });
      throw error;
    }
  }

  /**
   * Subscribe to a specific event type and bind to the queue
   * @param eventType The event type to subscribe to
   */
  private async subscribeToEventType(eventType: string): Promise<void> {
    if (!this.channel) return;

    const handler = this.handlers.get(eventType);

    if (!handler) {
      logger.warn(`No handler found for event type: ${eventType}`);
      return;
    }

    // Create routing key from event type
    const routingKey = eventType.replace(/\./g, '-');

    // Bind the queue to the exchange with the routing key
    await this.channel.bindQueue(this.options.queue, this.options.exchange, routingKey);

    // Start consuming messages
    const { consumerTag } = await this.channel.consume(
      this.options.queue,
      async (msg: ConsumeMessage | null) => {
        if (!msg) return;

        try {
          // Parse the event message
          const event = JSON.parse(msg.content.toString()) as EventMessage;

          // Process the event with the handler
          await handler(event);

          // Acknowledge the message
          this.channel?.ack(msg);
        } catch (error: any) {
          logger.error('Error processing RabbitMQ message', {
            error: error.message,
            routingKey: msg.fields.routingKey,
          });

          // Reject the message and requeue unless it's been retried too many times
          const retryCount = msg.properties.headers?.['x-retry-count'] || 0;

          if (retryCount < 3) {
            // Increment retry count
            if (!msg.properties.headers) {
              msg.properties.headers = {};
            }

            msg.properties.headers['x-retry-count'] = retryCount + 1;

            // Nack and requeue
            this.channel?.nack(msg, false, true);
          } else {
            // Max retries reached, reject without requeuing
            this.channel?.nack(msg, false, false);
          }
        }
      }
    );

    // Store the consumer tag
    this.consumerTags.set(eventType, consumerTag);
  }

  /**
   * Reconnect to RabbitMQ after a connection failure
   */
  private async reconnect(): Promise<void> {
    if (!this.options.autoReconnect) return;

    // Reset connection and channel
    this.connection = null;
    this.channel = null;

    let retryCount = 0;
    const maxRetries = 10;
    const initialDelay = 1000;

    const attemptReconnect = async (): Promise<void> => {
      try {
        logger.info(`Attempting to reconnect to RabbitMQ (attempt ${retryCount + 1}/${maxRetries})...`);
        await this.initialize();
        logger.info('Successfully reconnected to RabbitMQ');
      } catch (error: any) {
        retryCount++;

        if (retryCount >= maxRetries) {
          logger.error('Failed to reconnect to RabbitMQ after maximum retries', {
            error: error.message,
          });
          return;
        }

        const delay = initialDelay * Math.pow(2, retryCount);
        logger.info(`Retrying RabbitMQ connection in ${delay}ms...`);

        setTimeout(attemptReconnect, delay);
      }
    };

    // Start reconnection process
    setTimeout(attemptReconnect, initialDelay);
  }
}
