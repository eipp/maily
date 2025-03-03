import { Entity } from '../common/Entity';
import { Result } from '../common/Result';
import { CampaignId } from './CampaignTypes';
import { CampaignStatus } from './CampaignStatus';

/**
 * Campaign properties interface
 */
export interface CampaignProps {
  name: string;
  subject: string;
  content: string;
  status: CampaignStatus;
  sendAt?: Date;
  sentAt?: Date;
  contactListIds: string[];
  createdAt: Date;
  updatedAt: Date;
  userId: string;
  templateId?: string;
  tags?: string[];
}

/**
 * Campaign entity representing an email campaign
 */
export class Campaign extends Entity<CampaignId> {
  private readonly props: CampaignProps;

  private constructor(id: CampaignId, props: CampaignProps) {
    super(id);
    this.props = props;
  }

  /**
   * Creates a new Campaign entity.
   */
  public static create(
    id: CampaignId,
    props: Omit<CampaignProps, 'createdAt' | 'updatedAt' | 'status'>
  ): Result<Campaign, Error> {
    if (!props.name) {
      return Result.failure(new Error('Campaign name is required'));
    }

    if (!props.subject) {
      return Result.failure(new Error('Campaign subject is required'));
    }

    if (!props.content) {
      return Result.failure(new Error('Campaign content is required'));
    }

    if (!props.contactListIds || props.contactListIds.length === 0) {
      return Result.failure(new Error('Campaign must have at least one contact list'));
    }

    const now = new Date();
    
    return Result.success(
      new Campaign(id, {
        ...props,
        status: CampaignStatus.DRAFT,
        createdAt: now,
        updatedAt: now,
      })
    );
  }

  // Getters
  public get name(): string { return this.props.name; }
  public get subject(): string { return this.props.subject; }
  public get content(): string { return this.props.content; }
  public get status(): CampaignStatus { return this.props.status; }
  public get sendAt(): Date | undefined { return this.props.sendAt; }
  public get sentAt(): Date | undefined { return this.props.sentAt; }
  public get contactListIds(): string[] { return [...this.props.contactListIds]; }
  public get createdAt(): Date { return this.props.createdAt; }
  public get updatedAt(): Date { return this.props.updatedAt; }
  public get userId(): string { return this.props.userId; }
  public get templateId(): string | undefined { return this.props.templateId; }
  public get tags(): string[] | undefined { return this.props.tags ? [...this.props.tags] : undefined; }

  // Business logic
  public schedule(sendAt: Date): Result<void, Error> {
    if (this.props.status !== CampaignStatus.DRAFT) {
      return Result.failure(new Error('Only draft campaigns can be scheduled'));
    }

    if (sendAt <= new Date()) {
      return Result.failure(new Error('Schedule date must be in the future'));
    }

    this.props.sendAt = sendAt;
    this.props.status = CampaignStatus.SCHEDULED;
    this.props.updatedAt = new Date();
    
    return Result.success();
  }

  public markAsSent(): Result<void, Error> {
    if (this.props.status !== CampaignStatus.SENDING && this.props.status !== CampaignStatus.SCHEDULED) {
      return Result.failure(new Error('Only sending or scheduled campaigns can be marked as sent'));
    }

    this.props.status = CampaignStatus.SENT;
    this.props.sentAt = new Date();
    this.props.updatedAt = new Date();
    
    return Result.success();
  }

  public cancel(): Result<void, Error> {
    if (this.props.status !== CampaignStatus.SCHEDULED && this.props.status !== CampaignStatus.SENDING) {
      return Result.failure(new Error('Only scheduled or sending campaigns can be cancelled'));
    }

    this.props.status = CampaignStatus.CANCELLED;
    this.props.updatedAt = new Date();
    
    return Result.success();
  }

  public startSending(): Result<void, Error> {
    if (this.props.status !== CampaignStatus.SCHEDULED) {
      return Result.failure(new Error('Only scheduled campaigns can be started'));
    }

    this.props.status = CampaignStatus.SENDING;
    this.props.updatedAt = new Date();
    
    return Result.success();
  }

  public update(props: Partial<Pick<CampaignProps, 'name' | 'subject' | 'content' | 'contactListIds' | 'templateId' | 'tags'>>): Result<void, Error> {
    if (this.props.status !== CampaignStatus.DRAFT) {
      return Result.failure(new Error('Only draft campaigns can be updated'));
    }

    if (props.name !== undefined) {
      if (!props.name) {
        return Result.failure(new Error('Campaign name cannot be empty'));
      }
      this.props.name = props.name;
    }

    if (props.subject !== undefined) {
      if (!props.subject) {
        return Result.failure(new Error('Campaign subject cannot be empty'));
      }
      this.props.subject = props.subject;
    }

    if (props.content !== undefined) {
      if (!props.content) {
        return Result.failure(new Error('Campaign content cannot be empty'));
      }
      this.props.content = props.content;
    }

    if (props.contactListIds !== undefined) {
      if (!props.contactListIds.length) {
        return Result.failure(new Error('Campaign must have at least one contact list'));
      }
      this.props.contactListIds = props.contactListIds;
    }

    if (props.templateId !== undefined) {
      this.props.templateId = props.templateId;
    }

    if (props.tags !== undefined) {
      this.props.tags = props.tags;
    }

    this.props.updatedAt = new Date();
    
    return Result.success();
  }
}