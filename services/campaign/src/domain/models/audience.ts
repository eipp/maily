/**
 * Campaign Audience Value Object
 *
 * This represents the target audience for a campaign.
 */

import { AudienceType, RecipientStatus } from '../common/enums';
import { AudienceId, RecipientId, UserId } from '../common/identifiers';

/**
 * Recipient properties
 */
export interface RecipientProps {
  /**
   * Recipient ID
   */
  id: RecipientId;

  /**
   * Email address
   */
  email: string;

  /**
   * Recipient name
   */
  name?: string;

  /**
   * User ID (if associated with a user)
   */
  userId?: UserId;

  /**
   * Current status
   */
  status: RecipientStatus;

  /**
   * Custom attributes
   */
  attributes?: Record<string, any>;
}

/**
 * Audience filter criteria
 */
export interface AudienceFilter {
  /**
   * Filter field
   */
  field: string;

  /**
   * Filter operator
   */
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'in' | 'not_in';

  /**
   * Filter value
   */
  value: any;
}

/**
 * Audience properties
 */
export interface AudienceProps {
  /**
   * Audience ID
   */
  id: AudienceId;

  /**
   * Audience name
   */
  name: string;

  /**
   * Audience description
   */
  description?: string;

  /**
   * Audience type
   */
  type: AudienceType;

  /**
   * Static list of recipients (for STATIC type)
   */
  recipients?: RecipientProps[];

  /**
   * Segment filters (for SEGMENT type)
   */
  filters?: AudienceFilter[];

  /**
   * External source (for IMPORTED type)
   */
  source?: string;

  /**
   * Dynamic query (for DYNAMIC type)
   */
  query?: string;

  /**
   * Estimated size
   */
  estimatedSize?: number;

  /**
   * Tags
   */
  tags?: string[];

  /**
   * Creation date
   */
  createdAt?: Date;

  /**
   * Last modified date
   */
  updatedAt?: Date;
}

/**
 * Campaign Audience Value Object
 */
export class Audience {
  private readonly _id: AudienceId;
  private readonly _name: string;
  private readonly _description?: string;
  private readonly _type: AudienceType;
  private readonly _recipients: RecipientProps[];
  private readonly _filters: AudienceFilter[];
  private readonly _source?: string;
  private readonly _query?: string;
  private readonly _estimatedSize: number;
  private readonly _tags: string[];
  private readonly _createdAt: Date;
  private readonly _updatedAt: Date;

  /**
   * Create a new audience
   * @param props Audience properties
   */
  constructor(props: AudienceProps) {
    this._id = props.id;
    this._name = props.name;
    this._description = props.description;
    this._type = props.type;
    this._recipients = props.recipients ? [...props.recipients] : [];
    this._filters = props.filters ? [...props.filters] : [];
    this._source = props.source;
    this._query = props.query;
    this._estimatedSize = props.estimatedSize ?? 0;
    this._tags = props.tags ? [...props.tags] : [];
    this._createdAt = props.createdAt ?? new Date();
    this._updatedAt = props.updatedAt ?? new Date();

    this.validate();
  }

  // Getters
  public get id(): AudienceId { return this._id; }
  public get name(): string { return this._name; }
  public get description(): string | undefined { return this._description; }
  public get type(): AudienceType { return this._type; }
  public get recipients(): RecipientProps[] { return [...this._recipients]; }
  public get filters(): AudienceFilter[] { return [...this._filters]; }
  public get source(): string | undefined { return this._source; }
  public get query(): string | undefined { return this._query; }
  public get estimatedSize(): number { return this._estimatedSize; }
  public get size(): number { return this._recipients.length || this._estimatedSize; }
  public get tags(): string[] { return [...this._tags]; }
  public get createdAt(): Date { return new Date(this._createdAt); }
  public get updatedAt(): Date { return new Date(this._updatedAt); }

  /**
   * Validate audience configuration
   */
  private validate(): void {
    if (!this._name) {
      throw new Error('Audience name is required');
    }

    switch (this._type) {
      case AudienceType.STATIC:
        // Static audiences should have recipients
        if (this._recipients.length === 0) {
          throw new Error('Static audience must have recipients');
        }
        break;

      case AudienceType.SEGMENT:
        // Segment audiences should have filters
        if (this._filters.length === 0) {
          throw new Error('Segment audience must have filters');
        }
        break;

      case AudienceType.IMPORTED:
        // Imported audiences should have a source
        if (!this._source) {
          throw new Error('Imported audience must have a source');
        }
        break;

      case AudienceType.DYNAMIC:
        // Dynamic audiences should have a query
        if (!this._query) {
          throw new Error('Dynamic audience must have a query');
        }
        break;

      default:
        throw new Error(`Unknown audience type: ${this._type}`);
    }
  }

  /**
   * Check if audience is empty
   * @returns Whether audience is empty
   */
  public isEmpty(): boolean {
    return this.size === 0;
  }

  /**
   * Create a static audience from a list of recipients
   * @param id Audience ID
   * @param name Audience name
   * @param recipients List of recipients
   * @param description Optional description
   * @returns Static audience
   */
  public static createStatic(
    id: AudienceId,
    name: string,
    recipients: RecipientProps[],
    description?: string
  ): Audience {
    return new Audience({
      id,
      name,
      description,
      type: AudienceType.STATIC,
      recipients,
      estimatedSize: recipients.length,
    });
  }

  /**
   * Create a segment audience based on filters
   * @param id Audience ID
   * @param name Audience name
   * @param filters Segment filters
   * @param estimatedSize Estimated audience size
   * @param description Optional description
   * @returns Segment audience
   */
  public static createSegment(
    id: AudienceId,
    name: string,
    filters: AudienceFilter[],
    estimatedSize: number,
    description?: string
  ): Audience {
    return new Audience({
      id,
      name,
      description,
      type: AudienceType.SEGMENT,
      filters,
      estimatedSize,
    });
  }

  /**
   * Create an audience from an imported source
   * @param id Audience ID
   * @param name Audience name
   * @param source Source identifier
   * @param estimatedSize Estimated audience size
   * @param description Optional description
   * @returns Imported audience
   */
  public static createImported(
    id: AudienceId,
    name: string,
    source: string,
    estimatedSize: number,
    description?: string
  ): Audience {
    return new Audience({
      id,
      name,
      description,
      type: AudienceType.IMPORTED,
      source,
      estimatedSize,
    });
  }

  /**
   * Serialize to plain object
   * @returns Plain object representation
   */
  public toJSON(): Record<string, any> {
    return {
      id: this._id.value,
      name: this._name,
      description: this._description,
      type: this._type,
      recipients: this._recipients.map(r => ({
        id: r.id.value,
        email: r.email,
        name: r.name,
        userId: r.userId?.value,
        status: r.status,
        attributes: r.attributes,
      })),
      filters: this._filters,
      source: this._source,
      query: this._query,
      size: this.size,
      estimatedSize: this._estimatedSize,
      tags: this._tags,
      createdAt: this._createdAt.toISOString(),
      updatedAt: this._updatedAt.toISOString(),
    };
  }
}
