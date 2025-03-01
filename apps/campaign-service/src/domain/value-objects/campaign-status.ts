/**
 * Possible campaign statuses
 */
export enum CampaignStatusValue {
  DRAFT = 'DRAFT',
  SCHEDULED = 'SCHEDULED',
  SENDING = 'SENDING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  CANCELED = 'CANCELED',
  FAILED = 'FAILED',
}

/**
 * Campaign status value object
 */
export class CampaignStatus {
  private readonly value: CampaignStatusValue;

  private constructor(value: CampaignStatusValue) {
    this.value = value;
  }

  /**
   * Create a status from a status value
   * @param status The status value
   */
  public static create(status: CampaignStatusValue): CampaignStatus {
    return new CampaignStatus(status);
  }

  /**
   * Create a draft status
   */
  public static draft(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.DRAFT);
  }

  /**
   * Create a scheduled status
   */
  public static scheduled(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.SCHEDULED);
  }

  /**
   * Create a sending status
   */
  public static sending(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.SENDING);
  }

  /**
   * Create a paused status
   */
  public static paused(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.PAUSED);
  }

  /**
   * Create a completed status
   */
  public static completed(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.COMPLETED);
  }

  /**
   * Create a canceled status
   */
  public static canceled(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.CANCELED);
  }

  /**
   * Create a failed status
   */
  public static failed(): CampaignStatus {
    return new CampaignStatus(CampaignStatusValue.FAILED);
  }

  /**
   * Get the status value
   */
  public getValue(): CampaignStatusValue {
    return this.value;
  }

  /**
   * Check if status is a draft
   */
  public isDraft(): boolean {
    return this.value === CampaignStatusValue.DRAFT;
  }

  /**
   * Check if status is scheduled
   */
  public isScheduled(): boolean {
    return this.value === CampaignStatusValue.SCHEDULED;
  }

  /**
   * Check if status is sending
   */
  public isSending(): boolean {
    return this.value === CampaignStatusValue.SENDING;
  }

  /**
   * Check if status is paused
   */
  public isPaused(): boolean {
    return this.value === CampaignStatusValue.PAUSED;
  }

  /**
   * Check if status is completed
   */
  public isCompleted(): boolean {
    return this.value === CampaignStatusValue.COMPLETED;
  }

  /**
   * Check if status is canceled
   */
  public isCanceled(): boolean {
    return this.value === CampaignStatusValue.CANCELED;
  }

  /**
   * Check if status is failed
   */
  public isFailed(): boolean {
    return this.value === CampaignStatusValue.FAILED;
  }

  /**
   * Check if campaign can be scheduled
   */
  public canBeScheduled(): boolean {
    return this.isDraft();
  }

  /**
   * Check if campaign can be started
   */
  public canBeStarted(): boolean {
    return this.isDraft() || this.isScheduled() || this.isPaused();
  }

  /**
   * Check if campaign can be paused
   */
  public canBePaused(): boolean {
    return this.isSending();
  }

  /**
   * Check if campaign can be canceled
   */
  public canBeCanceled(): boolean {
    return this.isDraft() || this.isScheduled() || this.isSending() || this.isPaused();
  }

  /**
   * Check if campaign is in a terminal state
   */
  public isTerminal(): boolean {
    return this.isCompleted() || this.isCanceled() || this.isFailed();
  }

  /**
   * Check if status is equal to another status
   * @param other Other status to compare
   */
  public equals(other: CampaignStatus): boolean {
    return this.value === other.value;
  }

  /**
   * String representation of the status
   */
  public toString(): string {
    return this.value;
  }
}
