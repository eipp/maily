/**
 * Campaign Domain Model
 *
 * This module implements the core Campaign entity and related value objects
 * following Domain-Driven Design principles.
 */

import { Entity, AggregateRoot } from '../common/entity';
import { CampaignId, EmailId, UserId } from '../common/identifiers';
import {
  CampaignStatus,
  CampaignType,
  EmailDeliveryStatus,
  RecipientStatus
} from '../common/enums';
import { CampaignSchedule } from './schedule';
import { Audience } from './audience';
import { EmailTemplate } from './template';
import { CampaignSettings } from './settings';
import { DomainEvent } from '../events/domain-event';
import { CampaignCreatedEvent } from '../events/campaign-created';
import { CampaignUpdatedEvent } from '../events/campaign-updated';
import { CampaignLaunchedEvent } from '../events/campaign-launched';
import { CampaignPausedEvent } from '../events/campaign-paused';
import { CampaignCompletedEvent } from '../events/campaign-completed';
import { CampaignCanceledEvent } from '../events/campaign-canceled';

/**
 * Represents a Campaign entity as the aggregate root
 */
export class Campaign extends AggregateRoot<CampaignId> {
  private _name: string;
  private _description: string;
  private _type: CampaignType;
  private _status: CampaignStatus;
  private _createdBy: UserId;
  private _createdAt: Date;
  private _updatedAt: Date;
  private _audience: Audience;
  private _template: EmailTemplate;
  private _schedule: CampaignSchedule;
  private _settings: CampaignSettings;
  private _sentCount: number;
  private _openCount: number;
  private _clickCount: number;
  private _bounceCount: number;
  private _complaintCount: number;
  private _metadata: Record<string, any>;

  /**
   * Create a new Campaign entity
   * @param id Campaign ID
   * @param props Campaign properties
   */
  constructor(id: CampaignId, props: {
    name: string;
    description: string;
    type: CampaignType;
    createdBy: UserId;
    audience: Audience;
    template: EmailTemplate;
    schedule: CampaignSchedule;
    settings: CampaignSettings;
    status?: CampaignStatus;
    createdAt?: Date;
    updatedAt?: Date;
    sentCount?: number;
    openCount?: number;
    clickCount?: number;
    bounceCount?: number;
    complaintCount?: number;
    metadata?: Record<string, any>;
  }) {
    super(id);
    this._name = props.name;
    this._description = props.description;
    this._type = props.type;
    this._status = props.status || CampaignStatus.DRAFT;
    this._createdBy = props.createdBy;
    this._createdAt = props.createdAt || new Date();
    this._updatedAt = props.updatedAt || new Date();
    this._audience = props.audience;
    this._template = props.template;
    this._schedule = props.schedule;
    this._settings = props.settings;
    this._sentCount = props.sentCount || 0;
    this._openCount = props.openCount || 0;
    this._clickCount = props.clickCount || 0;
    this._bounceCount = props.bounceCount || 0;
    this._complaintCount = props.complaintCount || 0;
    this._metadata = props.metadata || {};
  }

  /**
   * Create a new Campaign
   * @param props Campaign creation properties
   * @returns New Campaign instance
   */
  public static create(props: {
    id?: CampaignId;
    name: string;
    description: string;
    type: CampaignType;
    createdBy: UserId;
    audience: Audience;
    template: EmailTemplate;
    schedule: CampaignSchedule;
    settings: CampaignSettings;
    metadata?: Record<string, any>;
  }): Campaign {
    const id = props.id || CampaignId.generate();
    const now = new Date();

    const campaign = new Campaign(id, {
      ...props,
      status: CampaignStatus.DRAFT,
      createdAt: now,
      updatedAt: now,
    });

    // Register creation event
    campaign.addDomainEvent(new CampaignCreatedEvent({
      campaignId: id,
      name: props.name,
      type: props.type,
      createdBy: props.createdBy,
      timestamp: now,
    }));

    return campaign;
  }

  // Getters for all properties
  public get name(): string { return this._name; }
  public get description(): string { return this._description; }
  public get type(): CampaignType { return this._type; }
  public get status(): CampaignStatus { return this._status; }
  public get createdBy(): UserId { return this._createdBy; }
  public get createdAt(): Date { return new Date(this._createdAt); }
  public get updatedAt(): Date { return new Date(this._updatedAt); }
  public get audience(): Audience { return this._audience; }
  public get template(): EmailTemplate { return this._template; }
  public get schedule(): CampaignSchedule { return this._schedule; }
  public get settings(): CampaignSettings { return this._settings; }
  public get sentCount(): number { return this._sentCount; }
  public get openCount(): number { return this._openCount; }
  public get clickCount(): number { return this._clickCount; }
  public get bounceCount(): number { return this._bounceCount; }
  public get complaintCount(): number { return this._complaintCount; }
  public get metadata(): Record<string, any> { return { ...this._metadata }; }

  // Campaign state transitions and operations

  /**
   * Update campaign details
   * @param props Properties to update
   */
  public update(props: {
    name?: string;
    description?: string;
    audience?: Audience;
    template?: EmailTemplate;
    schedule?: CampaignSchedule;
    settings?: CampaignSettings;
    metadata?: Record<string, any>;
  }): void {
    // Can only update in draft or scheduled status
    if (![CampaignStatus.DRAFT, CampaignStatus.SCHEDULED].includes(this._status)) {
      throw new Error(`Cannot update campaign in ${this._status} status`);
    }

    if (props.name) this._name = props.name;
    if (props.description) this._description = props.description;
    if (props.audience) this._audience = props.audience;
    if (props.template) this._template = props.template;
    if (props.schedule) this._schedule = props.schedule;
    if (props.settings) this._settings = props.settings;
    if (props.metadata) this._metadata = { ...this._metadata, ...props.metadata };

    this._updatedAt = new Date();

    // Register update event
    this.addDomainEvent(new CampaignUpdatedEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      updatedFields: Object.keys(props),
    }));
  }

  /**
   * Schedule the campaign for future delivery
   */
  public schedule(): void {
    // Can only schedule from draft state
    if (this._status !== CampaignStatus.DRAFT) {
      throw new Error(`Cannot schedule campaign in ${this._status} status`);
    }

    // Validate schedule
    if (!this._schedule.isValid()) {
      throw new Error('Invalid campaign schedule');
    }

    this._status = CampaignStatus.SCHEDULED;
    this._updatedAt = new Date();

    // Register scheduled event
    this.addDomainEvent(new CampaignUpdatedEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      updatedFields: ['status'],
      status: CampaignStatus.SCHEDULED,
    }));
  }

  /**
   * Launch the campaign immediately
   */
  public launch(): void {
    // Can only launch from draft or scheduled state
    if (![CampaignStatus.DRAFT, CampaignStatus.SCHEDULED].includes(this._status)) {
      throw new Error(`Cannot launch campaign in ${this._status} status`);
    }

    // Validate audience
    if (this._audience.isEmpty()) {
      throw new Error('Cannot launch campaign with empty audience');
    }

    // Validate template
    if (!this._template.isValid()) {
      throw new Error('Campaign template is not valid');
    }

    this._status = CampaignStatus.SENDING;
    this._updatedAt = new Date();

    // Register launched event
    this.addDomainEvent(new CampaignLaunchedEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      audienceSize: this._audience.size,
    }));
  }

  /**
   * Pause an in-progress campaign
   */
  public pause(): void {
    // Can only pause from sending state
    if (this._status !== CampaignStatus.SENDING) {
      throw new Error(`Cannot pause campaign in ${this._status} status`);
    }

    this._status = CampaignStatus.PAUSED;
    this._updatedAt = new Date();

    // Register paused event
    this.addDomainEvent(new CampaignPausedEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      sentCount: this._sentCount,
    }));
  }

  /**
   * Resume a paused campaign
   */
  public resume(): void {
    // Can only resume from paused state
    if (this._status !== CampaignStatus.PAUSED) {
      throw new Error(`Cannot resume campaign in ${this._status} status`);
    }

    this._status = CampaignStatus.SENDING;
    this._updatedAt = new Date();

    // Register resumed event
    this.addDomainEvent(new CampaignUpdatedEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      updatedFields: ['status'],
      status: CampaignStatus.SENDING,
    }));
  }

  /**
   * Cancel the campaign
   */
  public cancel(): void {
    // Can cancel from most states, except completed and canceled
    if ([CampaignStatus.COMPLETED, CampaignStatus.CANCELED].includes(this._status)) {
      throw new Error(`Cannot cancel campaign in ${this._status} status`);
    }

    this._status = CampaignStatus.CANCELED;
    this._updatedAt = new Date();

    // Register canceled event
    this.addDomainEvent(new CampaignCanceledEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      sentCount: this._sentCount,
    }));
  }

  /**
   * Mark campaign as completed
   */
  public complete(): void {
    // Can only complete from sending state
    if (this._status !== CampaignStatus.SENDING) {
      throw new Error(`Cannot complete campaign in ${this._status} status`);
    }

    this._status = CampaignStatus.COMPLETED;
    this._updatedAt = new Date();

    // Register completed event
    this.addDomainEvent(new CampaignCompletedEvent({
      campaignId: this.id,
      name: this._name,
      timestamp: this._updatedAt,
      sentCount: this._sentCount,
      openCount: this._openCount,
      clickCount: this._clickCount,
      bounceCount: this._bounceCount,
      complaintCount: this._complaintCount,
    }));
  }

  /**
   * Track email delivery
   * @param count Number of emails sent
   */
  public trackSent(count: number): void {
    if (count < 0) {
      throw new Error('Count must be a positive number');
    }

    this._sentCount += count;
    this._updatedAt = new Date();
  }

  /**
   * Track email opens
   * @param count Number of opens
   */
  public trackOpens(count: number): void {
    if (count < 0) {
      throw new Error('Count must be a positive number');
    }

    this._openCount += count;
    this._updatedAt = new Date();
  }

  /**
   * Track email clicks
   * @param count Number of clicks
   */
  public trackClicks(count: number): void {
    if (count < 0) {
      throw new Error('Count must be a positive number');
    }

    this._clickCount += count;
    this._updatedAt = new Date();
  }

  /**
   * Track email bounces
   * @param count Number of bounces
   */
  public trackBounces(count: number): void {
    if (count < 0) {
      throw new Error('Count must be a positive number');
    }

    this._bounceCount += count;
    this._updatedAt = new Date();
  }

  /**
   * Track email complaints
   * @param count Number of complaints
   */
  public trackComplaints(count: number): void {
    if (count < 0) {
      throw new Error('Count must be a positive number');
    }

    this._complaintCount += count;
    this._updatedAt = new Date();
  }

  /**
   * Get campaign performance metrics
   */
  public getPerformanceMetrics(): {
    deliveryRate: number;
    openRate: number;
    clickRate: number;
    bounceRate: number;
    complaintRate: number;
    clickToOpenRate: number;
  } {
    const deliveryRate = this._sentCount > 0
      ? (this._sentCount - this._bounceCount) / this._sentCount
      : 0;

    const openRate = this._sentCount > 0
      ? this._openCount / this._sentCount
      : 0;

    const clickRate = this._sentCount > 0
      ? this._clickCount / this._sentCount
      : 0;

    const bounceRate = this._sentCount > 0
      ? this._bounceCount / this._sentCount
      : 0;

    const complaintRate = this._sentCount > 0
      ? this._complaintCount / this._sentCount
      : 0;

    const clickToOpenRate = this._openCount > 0
      ? this._clickCount / this._openCount
      : 0;

    return {
      deliveryRate,
      openRate,
      clickRate,
      bounceRate,
      complaintRate,
      clickToOpenRate,
    };
  }

  /**
   * Serialize to plain object
   * @returns Plain object representation
   */
  public toJSON(): Record<string, any> {
    return {
      id: this.id.value,
      name: this._name,
      description: this._description,
      type: this._type,
      status: this._status,
      createdBy: this._createdBy.value,
      createdAt: this._createdAt.toISOString(),
      updatedAt: this._updatedAt.toISOString(),
      audience: this._audience.toJSON(),
      template: this._template.toJSON(),
      schedule: this._schedule.toJSON(),
      settings: this._settings.toJSON(),
      sentCount: this._sentCount,
      openCount: this._openCount,
      clickCount: this._clickCount,
      bounceCount: this._bounceCount,
      complaintCount: this._complaintCount,
      metadata: this._metadata,
      metrics: this.getPerformanceMetrics(),
    };
  }
}
