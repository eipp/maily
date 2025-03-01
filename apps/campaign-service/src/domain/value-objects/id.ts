import { v4 as uuidv4, validate as validateUuid } from 'uuid';

/**
 * ID value object
 * Universal identifier using UUID v4
 */
export class ID {
  private readonly value: string;

  private constructor(value: string) {
    this.value = value;
  }

  /**
   * Create a new ID with a random UUID
   */
  public static create(): ID {
    return new ID(uuidv4());
  }

  /**
   * Create an ID from an existing UUID
   * @param id UUID string
   */
  public static from(id: string): ID {
    if (!this.isValid(id)) {
      throw new Error(`Invalid ID: ${id}`);
    }

    return new ID(id);
  }

  /**
   * Check if a string is a valid UUID
   * @param id ID to validate
   */
  public static isValid(id: string): boolean {
    return validateUuid(id);
  }

  /**
   * Get the ID value
   */
  public getValue(): string {
    return this.value;
  }

  /**
   * Check if ID is equal to another ID
   * @param other Other ID to compare
   */
  public equals(other: ID): boolean {
    return this.value === other.value;
  }

  /**
   * String representation of the ID
   */
  public toString(): string {
    return this.value;
  }
}
