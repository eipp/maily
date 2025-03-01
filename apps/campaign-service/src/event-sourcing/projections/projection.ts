import { StoredEvent } from '../event-store/event-store';

/**
 * Interface for event projections that build read models from events
 */
export interface Projection<T> {
  /**
   * Name of the projection
   */
  name: string;

  /**
   * Event types this projection handles
   */
  eventTypes: string[];

  /**
   * Apply an event to the projection
   * @param event Event to apply
   */
  apply(event: StoredEvent): Promise<void>;

  /**
   * Get a read model by ID
   * @param id ID of the entity
   */
  get(id: string): Promise<T | null>;

  /**
   * Find read models by a query
   * @param query Query for finding read models
   */
  find(query: object): Promise<T[]>;

  /**
   * Count read models matching a query
   * @param query Query for counting read models
   */
  count(query: object): Promise<number>;

  /**
   * Reset the projection
   */
  reset(): Promise<void>;
}

/**
 * Base class for event handlers that know how to apply specific events
 */
export abstract class ProjectionHandler<T> {
  /**
   * Event type this handler can process
   */
  abstract eventType: string;

  /**
   * Apply an event to update a read model
   * @param event Event to apply
   * @param repository Repository for storing the read model
   */
  abstract handle(event: StoredEvent, repository: ProjectionRepository<T>): Promise<void>;
}

/**
 * Repository interface for storing and retrieving projection read models
 */
export interface ProjectionRepository<T> {
  /**
   * Save a read model
   * @param id ID of the entity
   * @param data Read model data
   */
  save(id: string, data: T): Promise<void>;

  /**
   * Get a read model by ID
   * @param id ID of the entity
   */
  get(id: string): Promise<T | null>;

  /**
   * Find read models by a query
   * @param query Query for finding read models
   */
  find(query: object): Promise<T[]>;

  /**
   * Count read models matching a query
   * @param query Query for counting read models
   */
  count(query: object): Promise<number>;

  /**
   * Delete a read model
   * @param id ID of the entity
   */
  delete(id: string): Promise<void>;

  /**
   * Clear all read models in this repository
   */
  clear(): Promise<void>;
}

/**
 * Position in the event stream
 */
export interface StreamPosition {
  /**
   * Last processed event ID
   */
  lastEventId?: string;

  /**
   * Last processed event timestamp
   */
  lastEventTimestamp?: Date;
}

/**
 * Service for managing projections
 */
export interface ProjectionManager {
  /**
   * Register a projection
   * @param projection Projection to register
   */
  register(projection: Projection<any>): void;

  /**
   * Start all registered projections
   */
  startAll(): Promise<void>;

  /**
   * Start a specific projection
   * @param name Projection name
   */
  start(name: string): Promise<void>;

  /**
   * Stop all projections
   */
  stopAll(): Promise<void>;

  /**
   * Stop a specific projection
   * @param name Projection name
   */
  stop(name: string): Promise<void>;

  /**
   * Reset a projection (clear and rebuild)
   * @param name Projection name
   */
  reset(name: string): Promise<void>;

  /**
   * Get the current stream position for a projection
   * @param name Projection name
   */
  getPosition(name: string): Promise<StreamPosition>;

  /**
   * Update the stream position for a projection
   * @param name Projection name
   * @param position New position
   */
  updatePosition(name: string, position: StreamPosition): Promise<void>;
}
