
import { DomainEvent } from '../../domain/events/campaign-events';

/**
 * Represents a stored event with metadata
 */
export interface StoredEvent<T extends DomainEvent = DomainEvent> {
  /**
   * Unique identifier of the event
   */
  id: string;

  /**
   * Event type
   */
  type: string;

  /**
   * ID of the aggregate the event belongs to
   */
  aggregateId: string;

  /**
   * Version of the aggregate after the event
   */
  version: number;

  /**
   * When the event occurred
   */
  timestamp: Date;

  /**
   * When the event was stored
   */
  storedAt: Date;

  /**
   * The actual event data
   */
  data: T;

  /**
   * Additional metadata for the event
   */
  metadata?: Record<string, any>;
}

/**
 * Event store interface for persisting and retrieving domain events
 */
export interface EventStore {
  /**
   * Store events for an aggregate
   * @param aggregateId Aggregate ID
   * @param events Events to store
   * @param expectedVersion Expected version for optimistic concurrency
   */
  appendEvents(
    aggregateId: string,
    events: DomainEvent[],
    expectedVersion?: number
  ): Promise<void>;

  /**
   * Get events for an aggregate
   * @param aggregateId Aggregate ID
   * @param fromVersion Optional starting version
   * @param toVersion Optional ending version
   */
  getEvents(
    aggregateId: string,
    fromVersion?: number,
    toVersion?: number
  ): Promise<StoredEvent[]>;

  /**
   * Get events of a specific type
   * @param eventType Event type
   * @param fromDate Optional starting date
   * @param toDate Optional ending date
   * @param limit Optional limit
   */
  getEventsByType(
    eventType: string,
    fromDate?: Date,
    toDate?: Date,
    limit?: number
  ): Promise<StoredEvent[]>;

  /**
   * Get the latest version of an aggregate
   * @param aggregateId Aggregate ID
   */
  getLatestVersion(aggregateId: string): Promise<number>;

  /**
   * Subscribe to events
   * @param eventTypes Event types to subscribe to
   * @param callback Callback function
   */
  subscribe(
    eventTypes: string[],
    callback: (event: StoredEvent) => Promise<void>
  ): Promise<Subscription>;
}

/**
 * Subscription interface for event subscriptions
 */
export interface Subscription {
  /**
   * Unsubscribe from events
   */
  unsubscribe(): Promise<void>;
}
