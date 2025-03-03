import { Identifier } from './Identifier';

/**
 * Abstract base class for all domain entities.
 * 
 * Entities are objects with a distinct identity that runs through time and
 * different states. They are defined by their identity, rather than their attributes.
 */
export abstract class Entity<T extends Identifier> {
  protected readonly _id: T;
  
  constructor(id: T) {
    this._id = id;
  }

  get id(): T {
    return this._id;
  }

  /**
   * Entities are compared based on their identifiers.
   */
  public equals(entity?: Entity<T>): boolean {
    if (entity === null || entity === undefined) {
      return false;
    }
    
    if (this === entity) {
      return true;
    }
    
    return this._id.equals(entity._id);
  }
}