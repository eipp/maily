/**
 * Base class for all identifiers in the domain model.
 * 
 * Identifiers provide a way to uniquely identify and reference entities.
 */
export abstract class Identifier {
  protected readonly value: string | number;
  
  constructor(value: string | number) {
    this.value = value;
  }
  
  /**
   * Returns the primitive value of the identifier.
   */
  public getValue(): string | number {
    return this.value;
  }
  
  /**
   * Checks if this identifier equals another identifier.
   */
  public equals(id?: Identifier): boolean {
    if (id === null || id === undefined) {
      return false;
    }
    
    if (!(id instanceof this.constructor)) {
      return false;
    }
    
    return this.value === id.value;
  }
  
  /**
   * Returns a string representation of the identifier.
   */
  public toString(): string {
    return String(this.value);
  }
}