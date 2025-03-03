/**
 * Campaign Schedule Value Object
 *
 * This represents the scheduling configuration for a campaign.
 */

import { ScheduleType } from '../common/enums';

/**
 * Campaign schedule properties
 */
export interface CampaignScheduleProps {
  /**
   * Schedule type
   */
  type: ScheduleType;

  /**
   * Scheduled start time
   */
  startTime?: Date;

  /**
   * Scheduled end time
   */
  endTime?: Date;

  /**
   * Time zone for scheduling
   */
  timeZone?: string;

  /**
   * Cron expression for recurring schedules
   */
  cronExpression?: string;

  /**
   * Days of week for recurring schedules (0-6, where 0 is Sunday)
   */
  daysOfWeek?: number[];

  /**
   * Whether to use recipient's local time zone
   */
  useRecipientTimeZone?: boolean;

  /**
   * Send optimization window start time (HH:MM)
   */
  optimizationWindowStart?: string;

  /**
   * Send optimization window end time (HH:MM)
   */
  optimizationWindowEnd?: string;
}

/**
 * Campaign Schedule Value Object
 */
export class CampaignSchedule {
  private readonly _type: ScheduleType;
  private readonly _startTime?: Date;
  private readonly _endTime?: Date;
  private readonly _timeZone: string;
  private readonly _cronExpression?: string;
  private readonly _daysOfWeek?: number[];
  private readonly _useRecipientTimeZone: boolean;
  private readonly _optimizationWindowStart?: string;
  private readonly _optimizationWindowEnd?: string;

  /**
   * Create a new campaign schedule
   * @param props Schedule properties
   */
  constructor(props: CampaignScheduleProps) {
    this._type = props.type;

    // Set start time if provided
    if (props.startTime) {
      this._startTime = new Date(props.startTime);
    }

    // Set end time if provided
    if (props.endTime) {
      this._endTime = new Date(props.endTime);
    }

    // Default to UTC if no time zone provided
    this._timeZone = props.timeZone || 'UTC';

    // Set cron expression for recurring schedules
    if (props.type === ScheduleType.RECURRING && props.cronExpression) {
      this._cronExpression = props.cronExpression;
    }

    // Set days of week for recurring schedules
    if (props.type === ScheduleType.RECURRING && props.daysOfWeek) {
      this._daysOfWeek = [...props.daysOfWeek];
    }

    // Set recipient time zone flag
    this._useRecipientTimeZone = props.useRecipientTimeZone || false;

    // Set optimization window
    if (props.type === ScheduleType.OPTIMAL_TIME) {
      this._optimizationWindowStart = props.optimizationWindowStart;
      this._optimizationWindowEnd = props.optimizationWindowEnd;
    }

    // Validate schedule
    this.validate();
  }

  // Getters
  public get type(): ScheduleType { return this._type; }
  public get startTime(): Date | undefined { return this._startTime ? new Date(this._startTime) : undefined; }
  public get endTime(): Date | undefined { return this._endTime ? new Date(this._endTime) : undefined; }
  public get timeZone(): string { return this._timeZone; }
  public get cronExpression(): string | undefined { return this._cronExpression; }
  public get daysOfWeek(): number[] | undefined { return this._daysOfWeek ? [...this._daysOfWeek] : undefined; }
  public get useRecipientTimeZone(): boolean { return this._useRecipientTimeZone; }
  public get optimizationWindowStart(): string | undefined { return this._optimizationWindowStart; }
  public get optimizationWindowEnd(): string | undefined { return this._optimizationWindowEnd; }

  /**
   * Validate schedule configuration
   */
  private validate(): void {
    // For scheduled type, start time is required
    if (this._type === ScheduleType.SCHEDULED && !this._startTime) {
      throw new Error('Scheduled campaigns must have a start time');
    }

    // If both start and end times are provided, end must be after start
    if (this._startTime && this._endTime && this._endTime <= this._startTime) {
      throw new Error('End time must be after start time');
    }

    // Validate recurring schedule
    if (this._type === ScheduleType.RECURRING) {
      if (!this._cronExpression && !this._daysOfWeek) {
        throw new Error('Recurring campaigns must define a schedule pattern');
      }
    }

    // Validate optimization window
    if (this._type === ScheduleType.OPTIMAL_TIME) {
      if (!this._optimizationWindowStart || !this._optimizationWindowEnd) {
        throw new Error('Optimal time campaigns must define an optimization window');
      }

      // Validate time format (HH:MM)
      const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;
      if (this._optimizationWindowStart && !timeRegex.test(this._optimizationWindowStart)) {
        throw new Error('Invalid optimization window start time format (use HH:MM)');
      }

      if (this._optimizationWindowEnd && !timeRegex.test(this._optimizationWindowEnd)) {
        throw new Error('Invalid optimization window end time format (use HH:MM)');
      }
    }
  }

  /**
   * Check if the schedule is valid and ready for execution
   * @returns Whether the schedule is valid
   */
  public isValid(): boolean {
    try {
      this.validate();

      // Check if start time is in the past for scheduled campaigns
      if (this._type === ScheduleType.SCHEDULED && this._startTime && this._startTime < new Date()) {
        return false;
      }

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if the campaign is due to start
   * @returns Whether the campaign should start now
   */
  public isDue(): boolean {
    const now = new Date();

    switch (this._type) {
      case ScheduleType.IMMEDIATE:
        return true;

      case ScheduleType.SCHEDULED:
        return this._startTime !== undefined && this._startTime <= now;

      case ScheduleType.RECURRING:
        // Would need to evaluate cron expression or days of week
        // This is a simplified implementation
        return false;

      case ScheduleType.OPTIMAL_TIME:
        // Would need to compute optimal times for recipients
        // This is a simplified implementation
        return false;

      default:
        return false;
    }
  }

  /**
   * Create an immediate schedule
   * @returns Immediate schedule
   */
  public static immediate(): CampaignSchedule {
    return new CampaignSchedule({
      type: ScheduleType.IMMEDIATE,
    });
  }

  /**
   * Create a scheduled campaign
   * @param startTime Start time
   * @param endTime Optional end time
   * @param timeZone Optional time zone
   * @returns Scheduled campaign
   */
  public static scheduled(startTime: Date, endTime?: Date, timeZone?: string): CampaignSchedule {
    return new CampaignSchedule({
      type: ScheduleType.SCHEDULED,
      startTime,
      endTime,
      timeZone,
    });
  }

  /**
   * Serialize to plain object
   * @returns Plain object representation
   */
  public toJSON(): Record<string, any> {
    return {
      type: this._type,
      startTime: this._startTime?.toISOString(),
      endTime: this._endTime?.toISOString(),
      timeZone: this._timeZone,
      cronExpression: this._cronExpression,
      daysOfWeek: this._daysOfWeek,
      useRecipientTimeZone: this._useRecipientTimeZone,
      optimizationWindowStart: this._optimizationWindowStart,
      optimizationWindowEnd: this._optimizationWindowEnd,
    };
  }
}
