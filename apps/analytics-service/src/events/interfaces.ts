/**
 * Event message interface
 */
export interface EventMessage {
  /** Unique event identifier */
  id: string;
  /** Event type identifier */
  type: string;
  /** Data payload */
  data: any;
  /** Event creation timestamp */
  timestamp: Date;
  /** Event source (service/component) */
  source: string;
  /** Optional correlation ID for tracing */
  correlationId?: string;
  /** Optional metadata */
  metadata?: Record<string, any>;
}

/**
 * Event publisher interface
 */
export interface EventPublisher {
  /**
   * Initialize the publisher
   */
  initialize(): Promise<void>;

  /**
   * Publish an event
   * @param event The event to publish
   */
  publish(event: EventMessage): Promise<void>;

  /**
   * Publish multiple events
   * @param events The events to publish
   */
  publishBatch(events: EventMessage[]): Promise<void>;

  /**
   * Close the publisher connection
   */
  close(): Promise<void>;
}

/**
 * Handler function for event subscribers
 */
export type EventHandler = (event: EventMessage) => Promise<void>;

/**
 * Event subscriber interface
 */
export interface EventSubscriber {
  /**
   * Initialize the subscriber
   */
  initialize(): Promise<void>;

  /**
   * Subscribe to an event type
   * @param eventType The event type to subscribe to
   * @param handler The handler function for events
   */
  subscribe(eventType: string, handler: EventHandler): Promise<void>;

  /**
   * Subscribe to multiple event types
   * @param eventTypes The event types to subscribe to
   * @param handler The handler function for events
   */
  subscribeMultiple(eventTypes: string[], handler: EventHandler): Promise<void>;

  /**
   * Unsubscribe from an event type
   * @param eventType The event type to unsubscribe from
   */
  unsubscribe(eventType: string): Promise<void>;

  /**
   * Close the subscriber connection
   */
  close(): Promise<void>;
}

/**
 * Generic options for message brokers
 */
export interface BrokerOptions {
  /** Connection URL */
  url: string;
  /** Exchange or topic name */
  exchange: string;
  /** Queue name */
  queue: string;
  /** Client identifier */
  clientId?: string;
  /** Connection timeout in milliseconds */
  connectionTimeout?: number;
  /** Auto reconnect flag */
  autoReconnect?: boolean;
  /** Credentials for authentication */
  credentials?: {
    username: string;
    password: string;
  };
  /** SSL/TLS options */
  ssl?: {
    enabled: boolean;
    rejectUnauthorized?: boolean;
    ca?: string;
    cert?: string;
    key?: string;
  };
  /** Additional options specific to the broker implementation */
  [key: string]: any;
}
