/**
 * Interface that all value objects must implement.
 * 
 * Value objects are objects that we determine their equality through their structural property.
 */
export interface ValueObject<T> {
  /**
   * Checks if this value object equals another value object.
   */
  equals(other: ValueObject<T>): boolean;
}

/**
 * Abstract base class for simple value objects.
 */
export abstract class SimpleValueObject<T> implements ValueObject<T> {
  protected readonly props: T;
  
  constructor(props: T) {
    this.props = props;
  }
  
  /**
   * Returns the underlying value of this value object.
   */
  public getValue(): T {
    return this.props;
  }
  
  /**
   * Checks if this value object equals another value object.
   */
  public equals(other?: ValueObject<T>): boolean {
    if (other === null || other === undefined) {
      return false;
    }
    
    if (!(other instanceof this.constructor)) {
      return false;
    }
    
    return this.equalsCore(other as SimpleValueObject<T>);
  }
  
  /**
   * Core equality logic for comparing value objects of the same type.
   */
  protected equalsCore(other: SimpleValueObject<T>): boolean {
    return JSON.stringify(this.props) === JSON.stringify(other.props);
  }
}