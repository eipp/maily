/**
 * Domain identifiers
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * Base identifier value object
 */
export abstract class Identifier<T> {
  constructor(private readonly _value: T) {
    this._value = _value;
  }

  /**
   * Get the identifier value
   */
  public get value(): T {
    return this._value;
  }

  /**
   * Compare with another identifier
   * @param id Identifier to compare with
   * @returns Whether the identifiers are equal
   */
  public equals(id?: Identifier<T>): boolean {
    if (id === null || id === undefined) {
      return false;
    }

    if (!(id instanceof this.constructor)) {
      return false;
    }

    return this._value === id.value;
  }

  /**
   * Convert to string
   * @returns String representation
   */
  public toString(): string {
    return String(this._value);
  }

  /**
   * Convert to primitive value
   * @returns Primitive value
   */
  public valueOf(): T {
    return this._value;
  }
}

/**
 * Campaign identifier
 */
export class CampaignId extends Identifier<string> {
  private constructor(id: string) {
    super(id);

    // Validate UUID format
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
      throw new Error('Invalid campaign ID format');
    }
  }

  /**
   * Create a campaign ID from an existing string
   * @param id ID string
   * @returns Campaign ID
   */
  public static fromString(id: string): CampaignId {
    return new CampaignId(id);
  }

  /**
   * Generate a new campaign ID
   * @returns Campaign ID
   */
  public static generate(): CampaignId {
    return new CampaignId(uuidv4());
  }
}

/**
 * User identifier
 */
export class UserId extends Identifier<string> {
  private constructor(id: string) {
    super(id);

    if (!id) {
      throw new Error('User ID cannot be empty');
    }
  }

  /**
   * Create a user ID from an existing string
   * @param id ID string
   * @returns User ID
   */
  public static fromString(id: string): UserId {
    return new UserId(id);
  }
}

/**
 * Email identifier
 */
export class EmailId extends Identifier<string> {
  private constructor(id: string) {
    super(id);

    // Validate UUID format
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
      throw new Error('Invalid email ID format');
    }
  }

  /**
   * Create an email ID from an existing string
   * @param id ID string
   * @returns Email ID
   */
  public static fromString(id: string): EmailId {
    return new EmailId(id);
  }

  /**
   * Generate a new email ID
   * @returns Email ID
   */
  public static generate(): EmailId {
    return new EmailId(uuidv4());
  }
}

/**
 * Template identifier
 */
export class TemplateId extends Identifier<string> {
  private constructor(id: string) {
    super(id);

    if (!id) {
      throw new Error('Template ID cannot be empty');
    }
  }

  /**
   * Create a template ID from an existing string
   * @param id ID string
   * @returns Template ID
   */
  public static fromString(id: string): TemplateId {
    return new TemplateId(id);
  }

  /**
   * Generate a new template ID
   * @returns Template ID
   */
  public static generate(): TemplateId {
    return new TemplateId(uuidv4());
  }
}

/**
 * Audience identifier
 */
export class AudienceId extends Identifier<string> {
  private constructor(id: string) {
    super(id);

    if (!id) {
      throw new Error('Audience ID cannot be empty');
    }
  }

  /**
   * Create an audience ID from an existing string
   * @param id ID string
   * @returns Audience ID
   */
  public static fromString(id: string): AudienceId {
    return new AudienceId(id);
  }

  /**
   * Generate a new audience ID
   * @returns Audience ID
   */
  public static generate(): AudienceId {
    return new AudienceId(uuidv4());
  }
}

/**
 * Recipient identifier
 */
export class RecipientId extends Identifier<string> {
  private constructor(id: string) {
    super(id);

    if (!id) {
      throw new Error('Recipient ID cannot be empty');
    }
  }

  /**
   * Create a recipient ID from an existing string
   * @param id ID string
   * @returns Recipient ID
   */
  public static fromString(id: string): RecipientId {
    return new RecipientId(id);
  }
}
