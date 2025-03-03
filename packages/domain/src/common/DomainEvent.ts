/**
 * Interface for all domain events.
 * 
 * Domain events represent something that happened in the domain that domain 
 * experts care about. They are named with a past-tense verb.
 */
export interface DomainEvent {
  /**
   * The date when the event occurred.
   */
  readonly occurredAt: Date;
  
  /**
   * Returns the name of the event.
   */
  eventName(): string;
}

/**
 * Base class for all domain events.
 */
export abstract class BaseDomainEvent implements DomainEvent {
  public readonly occurredAt: Date;
  
  constructor() {
    this.occurredAt = new Date();
  }
  
  /**
   * Returns the name of the event based on the class name.
   */
  public eventName(): string {
    return this.constructor.name;
  }
}

/**
 * Interface for domain event handlers.
 */
export interface DomainEventHandler<T extends DomainEvent> {
  /**
   * Handles a domain event.
   */
  handle(event: T): Promise<void>;
}

/**
 * Interface for domain event dispatchers.
 */
export interface DomainEventDispatcher {
  /**
   * Dispatches a domain event to its handlers.
   */
  dispatch<T extends DomainEvent>(event: T): Promise<void>;
  
  /**
   * Registers a handler for a domain event.
   */
  register<T extends DomainEvent>(
    eventClass: new (...args: any[]) => T,
    handler: DomainEventHandler<T>
  ): void;
}