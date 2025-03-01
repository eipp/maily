import { ID } from '../value-objects/id';
import { EmailAddress } from '../value-objects/email-address';
import { CampaignStatus, CampaignStatusValue } from '../value-objects/campaign-status';

/**
 * Campaign Entity - Aggregate Root
 * The central entity in the Campaign domain
 */
export class Campaign {
  private _id: ID;
  private _name: string;
  private _description: string;
  private _subject: string;
  private _content: string;
  private _contentType: 'html' | 'text';
  private _fromName: string;
  private _fromEmail: EmailAddress;
  private _replyToEmail: EmailAddress | null;
  private _status: CampaignStatus;
  private _createdAt: Date;
  private _updatedAt: Date;
  private _scheduledAt: Date | null;
  private _sentAt: Date | null;
  private _completedAt: Date | null;
  private _segmentId: ID | null;
  private _templateId: ID | null;
  private _version: number;
  private _metadata: Record<string, any>;

  private constructor(
    id: ID,
    name: string,
    description: string,
    subject: string,
    content: string,
    contentType: 'html' | 'text',
    fromName: string,
    fromEmail: EmailAddress,
    replyToEmail: EmailAddress | null,
    status: CampaignStatus,
    createdAt: Date,
    updatedAt: Date,
    scheduledAt: Date | null,
    sentAt: Date | null,
    completedAt: Date | null,
    segmentId: ID | null,
    templateId: ID | null,
    version: number,
    metadata: Record<string, any>
  ) {
    this._id = id;
    this._name = name;
    this._description = description;
    this._subject = subject;
    this._content = content;
    this._contentType = contentType;
    this._fromName = fromName;
    this._fromEmail = fromEmail;
    this._replyToEmail = replyToEmail;
    this._status = status;
    this._createdAt = createdAt;
    this._updatedAt = updatedAt;
    this._scheduledAt = scheduledAt;
    this._sentAt = sentAt;
    this._completedAt = completedAt;
    this._segmentId = segmentId;
    this._templateId = templateId;
    this._version = version;
    this._metadata = metadata;
  }

  /**
   * Create a new Campaign
   */
  public static create(
    name: string,
    subject: string,
    content: string,
    fromName: string,
    fromEmail: EmailAddress,
    options: {
      description?: string;
      contentType?: 'html' | 'text';
      replyToEmail?: EmailAddress;
      segmentId?: ID;
      templateId?: ID;
      metadata?: Record<string, any>;
    } = {}
  ): Campaign {
    const now = new Date();

    return new Campaign(
      ID.create(),
      name,
      options.description || '',
      subject,
      content,
      options.contentType || 'html',
      fromName,
      fromEmail,
      options.replyToEmail || null,
      CampaignStatus.draft(),
      now,
      now,
      null,
      null,
      null,
      options.segmentId || null,
      options.templateId || null,
      1,
      options.metadata || {}
    );
  }

  /**
   * Reconstruct a Campaign from persisted data
   */
  public static reconstitute(
    id: ID,
    name: string,
    description: string,
    subject: string,
    content: string,
    contentType: 'html' | 'text',
    fromName: string,
    fromEmail: EmailAddress,
    status: CampaignStatus,
    createdAt: Date,
    updatedAt: Date,
    version: number,
    options: {
      replyToEmail?: EmailAddress;
      scheduledAt?: Date;
      sentAt?: Date;
      completedAt?: Date;
      segmentId?: ID;
      templateId?: ID;
      metadata?: Record<string, any>;
    } = {}
  ): Campaign {
    return new Campaign(
      id,
      name,
      description,
      subject,
      content,
      contentType,
      fromName,
      fromEmail,
      options.replyToEmail || null,
      status,
      createdAt,
      updatedAt,
      options.scheduledAt || null,
      options.sentAt || null,
      options.completedAt || null,
      options.segmentId || null,
      options.templateId || null,
      version,
      options.metadata || {}
    );
  }

  // Getters

  public get id(): ID {
    return this._id;
  }

  public get name(): string {
    return this._name;
  }

  public get description(): string {
    return this._description;
  }

  public get subject(): string {
    return this._subject;
  }

  public get content(): string {
    return this._content;
  }

  public get contentType(): 'html' | 'text' {
    return this._contentType;
  }

  public get fromName(): string {
    return this._fromName;
  }

  public get fromEmail(): EmailAddress {
    return this._fromEmail;
  }

  public get replyToEmail(): EmailAddress | null {
    return this._replyToEmail;
  }

  public get status(): CampaignStatus {
    return this._status;
  }

  public get createdAt(): Date {
    return this._createdAt;
  }

  public get updatedAt(): Date {
    return this._updatedAt;
  }

  public get scheduledAt(): Date | null {
    return this._scheduledAt;
  }

  public get sentAt(): Date | null {
    return this._sentAt;
  }

  public get completedAt(): Date | null {
    return this._completedAt;
  }

  public get segmentId(): ID | null {
    return this._segmentId;
  }

  public get templateId(): ID | null {
    return this._templateId;
  }

  public get version(): number {
    return this._version;
  }

  public get metadata(): Record<string, any> {
    return { ...this._metadata };
  }

  // Business logic methods

  /**
   * Update campaign details
   */
  public update(
    name: string,
    subject: string,
    content: string,
    fromName: string,
    fromEmail: EmailAddress,
    options: {
      description?: string;
      contentType?: 'html' | 'text';
      replyToEmail?: EmailAddress;
      segmentId?: ID;
      templateId?: ID;
      metadata?: Record<string, any>;
    } = {}
  ): void {
    if (!this._status.isDraft()) {
      throw new Error('Can only update campaigns in draft status');
    }

    this._name = name;
    this._subject = subject;
    this._content = content;
    this._fromName = fromName;
    this._fromEmail = fromEmail;

    if (options.description !== undefined) {
      this._description = options.description;
    }

    if (options.contentType !== undefined) {
      this._contentType = options.contentType;
    }

    if (options.replyToEmail !== undefined) {
      this._replyToEmail = options.replyToEmail;
    }

    if (options.segmentId !== undefined) {
      this._segmentId = options.segmentId;
    }

    if (options.templateId !== undefined) {
      this._templateId = options.templateId;
    }

    if (options.metadata !== undefined) {
      this._metadata = { ...this._metadata, ...options.metadata };
    }

    this._updatedAt = new Date();
    this._version += 1;
  }

  /**
   * Schedule the campaign for sending at a specific time
   */
  public schedule(scheduledAt: Date): void {
    if (!this._status.canBeScheduled()) {
      throw new Error(`Cannot schedule campaign with status: ${this._status.getValue()}`);
    }

    if (scheduledAt <= new Date()) {
      throw new Error('Scheduled date must be in the future');
    }

    this._status = CampaignStatus.scheduled();
    this._scheduledAt = scheduledAt;
    this._updatedAt = new Date();
    this._version += 1;
  }

  /**
   * Start sending the campaign immediately
   */
  public send(): void {
    if (!this._status.canBeStarted()) {
      throw new Error(`Cannot start campaign with status: ${this._status.getValue()}`);
    }

    if (this._segmentId === null) {
      throw new Error('Campaign must have a segment to be sent');
    }

    const now = new Date();
    this._status = CampaignStatus.sending();
    this._sentAt = this._sentAt || now;
    this._updatedAt = now;
    this._version += 1;
  }

  /**
   * Pause a sending campaign
   */
  public pause(): void {
    if (!this._status.canBePaused()) {
      throw new Error(`Cannot pause campaign with status: ${this._status.getValue()}`);
    }

    this._status = CampaignStatus.paused();
    this._updatedAt = new Date();
    this._version += 1;
  }

  /**
   * Cancel the campaign
   */
  public cancel(): void {
    if (!this._status.canBeCanceled()) {
      throw new Error(`Cannot cancel campaign with status: ${this._status.getValue()}`);
    }

    this._status = CampaignStatus.canceled();
    this._updatedAt = new Date();
    this._version += 1;
  }

  /**
   * Mark campaign as completed
   */
  public complete(): void {
    if (!this._status.isSending()) {
      throw new Error('Only sending campaigns can be completed');
    }

    this._status = CampaignStatus.completed();
    this._completedAt = new Date();
    this._updatedAt = new Date();
    this._version += 1;
  }

  /**
   * Mark campaign as failed
   */
  public fail(reason: string): void {
    if (this._status.isTerminal()) {
      throw new Error('Cannot mark a terminal campaign as failed');
    }

    this._status = CampaignStatus.failed();
    this._metadata = {
      ...this._metadata,
      failureReason: reason,
      failedAt: new Date().toISOString(),
    };
    this._updatedAt = new Date();
    this._version += 1;
  }

  /**
   * Check if two campaigns are the same entity
   */
  public equals(other: Campaign): boolean {
    return this._id.equals(other.id);
  }
}
