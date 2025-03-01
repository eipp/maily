/**
 * Base domain event class
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * Base domain event interface
 */
export interface DomainEvent {
  /**
   * Event ID
   */
  eventId: string;

  /**
   * Event timestamp
   */
  timestamp: Date;

  /**
   * Event type
   */
  eventType: string;

  /**
   * Event version
   */
  eventVersion: number;
}

/**
 * Base domain event implementation
 */
export abstract class BaseDomainEvent implements DomainEvent {
  public readonly eventId: string;
  public readonly timestamp: Date;
  public readonly eventVersion: number;

  /**
   * Create a new domain event
   * @param eventType Event type
   * @param payload Event payload
   * @param timestamp Event timestamp
   */
  constructor(
    public readonly eventType: string,
    public readonly payload: Record<string, any>,
    timestamp?: Date
  ) {
    this.eventId = uuidv4();
    this.timestamp = timestamp || new Date();
    this.eventVersion = 1; // Default version, can be overridden in subclasses
  }

  /**
   * Serialize the event to JSON
   * @returns JSON representation
   */
  public toJSON(): Record<string, any> {
    return {
      eventId: this.eventId,
      eventType: this.eventType,
      eventVersion: this.eventVersion,
      timestamp: this.timestamp.toISOString(),
      payload: this.payload,
    };
  }
}
