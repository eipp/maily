/**
 * Campaign Settings Value Object
 *
 * This represents configuration settings for a campaign.
 */

/**
 * Campaign settings properties
 */
export interface CampaignSettingsProps {
  /**
   * Track email opens
   */
  trackOpens?: boolean;

  /**
   * Track email clicks
   */
  trackClicks?: boolean;

  /**
   * Track replies
   */
  trackReplies?: boolean;

  /**
   * Send rate limit (emails per minute)
   */
  sendRateLimit?: number;

  /**
   * Delivery priority (1-10, higher is higher priority)
   */
  deliveryPriority?: number;

  /**
   * Authentication domain for DKIM
   */
  authenticationDomain?: string;

  /**
   * Google Analytics tracking parameters
   */
  googleAnalytics?: {
    /**
     * UTM source
     */
    utmSource?: string;

    /**
     * UTM medium
     */
    utmMedium?: string;

    /**
     * UTM campaign
     */
    utmCampaign?: string;

    /**
     * UTM term
     */
    utmTerm?: string;

    /**
     * UTM content
     */
    utmContent?: string;
  };

  /**
   * Email service provider to use
   */
  emailProvider?: string;

  /**
   * Whether to use a custom SMTP server
   */
  useCustomSmtp?: boolean;

  /**
   * Custom SMTP settings
   */
  smtpSettings?: {
    /**
     * SMTP host
     */
    host: string;

    /**
     * SMTP port
     */
    port: number;

    /**
     * SMTP username
     */
    username: string;

    /**
     * SMTP password
     */
    password: string;

    /**
     * Whether to use TLS
     */
    useTls: boolean;
  };

  /**
   * Whether to enable automatic retry for failed deliveries
   */
  enableRetries?: boolean;

  /**
   * Maximum number of retries
   */
  maxRetries?: number;

  /**
   * Retry delay in minutes
   */
  retryDelayMinutes?: number;

  /**
   * IP pool to use for sending
   */
  ipPool?: string;

  /**
   * Email headers to include
   */
  headers?: Record<string, string>;

  /**
   * Whether to include unsubscribe link
   */
  includeUnsubscribeLink?: boolean;

  /**
   * Custom unsubscribe link
   */
  customUnsubscribeLink?: string;

  /**
   * Footer to append to the email
   */
  footer?: string;

  /**
   * Content personalization options
   */
  personalization?: {
    /**
     * Whether to enable personalization
     */
    enabled: boolean;

    /**
     * Default values for missing variables
     */
    defaultValues?: Record<string, string>;

    /**
     * Fallback strategy for missing values
     * - remove: Remove the variable placeholder
     * - keep: Keep the variable placeholder as is
     * - default: Use default values
     */
    fallbackStrategy?: 'remove' | 'keep' | 'default';
  };

  /**
   * A/B testing settings
   */
  abTesting?: {
    /**
     * Whether A/B testing is enabled
     */
    enabled: boolean;

    /**
     * Test variants
     */
    variants: Array<{
      /**
       * Variant name
       */
      name: string;

      /**
       * Subject line for this variant
       */
      subject?: string;

      /**
       * From name for this variant
       */
      fromName?: string;

      /**
       * Percentage of recipients to receive this variant
       */
      percentage: number;
    }>;

    /**
     * Winning criteria
     */
    winningCriteria?: 'opens' | 'clicks' | 'conversions';

    /**
     * Test duration in hours
     */
    testDurationHours?: number;

    /**
     * Whether to automatically send the winner after the test
     */
    sendWinnerAutomatically?: boolean;
  };
}

/**
 * Campaign Settings Value Object
 */
export class CampaignSettings {
  private readonly _trackOpens: boolean;
  private readonly _trackClicks: boolean;
  private readonly _trackReplies: boolean;
  private readonly _sendRateLimit?: number;
  private readonly _deliveryPriority: number;
  private readonly _authenticationDomain?: string;
  private readonly _googleAnalytics?: {
    utmSource?: string;
    utmMedium?: string;
    utmCampaign?: string;
    utmTerm?: string;
    utmContent?: string;
  };
  private readonly _emailProvider?: string;
  private readonly _useCustomSmtp: boolean;
  private readonly _smtpSettings?: {
    host: string;
    port: number;
    username: string;
    password: string;
    useTls: boolean;
  };
  private readonly _enableRetries: boolean;
  private readonly _maxRetries: number;
  private readonly _retryDelayMinutes: number;
  private readonly _ipPool?: string;
  private readonly _headers: Record<string, string>;
  private readonly _includeUnsubscribeLink: boolean;
  private readonly _customUnsubscribeLink?: string;
  private readonly _footer?: string;
  private readonly _personalization: {
    enabled: boolean;
    defaultValues: Record<string, string>;
    fallbackStrategy: 'remove' | 'keep' | 'default';
  };
  private readonly _abTesting?: {
    enabled: boolean;
    variants: Array<{
      name: string;
      subject?: string;
      fromName?: string;
      percentage: number;
    }>;
    winningCriteria?: 'opens' | 'clicks' | 'conversions';
    testDurationHours?: number;
    sendWinnerAutomatically?: boolean;
  };

  /**
   * Create new campaign settings
   * @param props Settings properties
   */
  constructor(props: CampaignSettingsProps = {}) {
    this._trackOpens = props.trackOpens ?? true;
    this._trackClicks = props.trackClicks ?? true;
    this._trackReplies = props.trackReplies ?? false;
    this._sendRateLimit = props.sendRateLimit;
    this._deliveryPriority = props.deliveryPriority ?? 5;
    this._authenticationDomain = props.authenticationDomain;
    this._googleAnalytics = props.googleAnalytics ? { ...props.googleAnalytics } : undefined;
    this._emailProvider = props.emailProvider;
    this._useCustomSmtp = props.useCustomSmtp ?? false;
    this._smtpSettings = props.smtpSettings ? { ...props.smtpSettings } : undefined;
    this._enableRetries = props.enableRetries ?? true;
    this._maxRetries = props.maxRetries ?? 3;
    this._retryDelayMinutes = props.retryDelayMinutes ?? 15;
    this._ipPool = props.ipPool;
    this._headers = props.headers ? { ...props.headers } : {};
    this._includeUnsubscribeLink = props.includeUnsubscribeLink ?? true;
    this._customUnsubscribeLink = props.customUnsubscribeLink;
    this._footer = props.footer;

    this._personalization = {
      enabled: props.personalization?.enabled ?? true,
      defaultValues: props.personalization?.defaultValues ?? {},
      fallbackStrategy: props.personalization?.fallbackStrategy ?? 'default',
    };

    if (props.abTesting?.enabled) {
      this._abTesting = {
        enabled: true,
        variants: [...props.abTesting.variants],
        winningCriteria: props.abTesting.winningCriteria ?? 'opens',
        testDurationHours: props.abTesting.testDurationHours ?? 24,
        sendWinnerAutomatically: props.abTesting.sendWinnerAutomatically ?? true,
      };

      this.validateAbTesting();
    } else {
      this._abTesting = undefined;
    }
  }

  // Getters
  public get trackOpens(): boolean { return this._trackOpens; }
  public get trackClicks(): boolean { return this._trackClicks; }
  public get trackReplies(): boolean { return this._trackReplies; }
  public get sendRateLimit(): number | undefined { return this._sendRateLimit; }
  public get deliveryPriority(): number { return this._deliveryPriority; }
  public get authenticationDomain(): string | undefined { return this._authenticationDomain; }
  public get googleAnalytics() { return this._googleAnalytics ? { ...this._googleAnalytics } : undefined; }
  public get emailProvider(): string | undefined { return this._emailProvider; }
  public get useCustomSmtp(): boolean { return this._useCustomSmtp; }
  public get smtpSettings() { return this._smtpSettings ? { ...this._smtpSettings } : undefined; }
  public get enableRetries(): boolean { return this._enableRetries; }
  public get maxRetries(): number { return this._maxRetries; }
  public get retryDelayMinutes(): number { return this._retryDelayMinutes; }
  public get ipPool(): string | undefined { return this._ipPool; }
  public get headers(): Record<string, string> { return { ...this._headers }; }
  public get includeUnsubscribeLink(): boolean { return this._includeUnsubscribeLink; }
  public get customUnsubscribeLink(): string | undefined { return this._customUnsubscribeLink; }
  public get footer(): string | undefined { return this._footer; }
  public get personalization() {
    return {
      enabled: this._personalization.enabled,
      defaultValues: { ...this._personalization.defaultValues },
      fallbackStrategy: this._personalization.fallbackStrategy,
    };
  }
  public get abTesting() {
    if (!this._abTesting) return undefined;
    return {
      enabled: this._abTesting.enabled,
      variants: [...this._abTesting.variants],
      winningCriteria: this._abTesting.winningCriteria,
      testDurationHours: this._abTesting.testDurationHours,
      sendWinnerAutomatically: this._abTesting.sendWinnerAutomatically,
    };
  }

  /**
   * Validate A/B testing configuration
   */
  private validateAbTesting(): void {
    if (!this._abTesting) return;

    // Ensure there are at least two variants
    if (this._abTesting.variants.length < 2) {
      throw new Error('A/B testing requires at least two variants');
    }

    // Ensure variant names are unique
    const variantNames = new Set<string>();
    for (const variant of this._abTesting.variants) {
      if (variantNames.has(variant.name)) {
        throw new Error(`Duplicate variant name: ${variant.name}`);
      }
      variantNames.add(variant.name);

      // Ensure percentage is valid
      if (variant.percentage <= 0 || variant.percentage > 100) {
        throw new Error(`Invalid percentage for variant ${variant.name}: ${variant.percentage}`);
      }
    }

    // Ensure percentages sum up to 100%
    const totalPercentage = this._abTesting.variants.reduce(
      (sum, variant) => sum + variant.percentage,
      0
    );

    if (Math.abs(totalPercentage - 100) > 0.1) {
      throw new Error(`A/B testing variant percentages must sum to 100%, got ${totalPercentage}%`);
    }
  }

  /**
   * Create default settings
   * @returns Default campaign settings
   */
  public static createDefault(): CampaignSettings {
    return new CampaignSettings();
  }

  /**
   * Create high priority settings
   * @returns High priority campaign settings
   */
  public static createHighPriority(): CampaignSettings {
    return new CampaignSettings({
      deliveryPriority: 10,
      enableRetries: true,
      maxRetries: 5,
      retryDelayMinutes: 5,
    });
  }

  /**
   * Serialize to plain object
   * @returns Plain object representation
   */
  public toJSON(): Record<string, any> {
    return {
      trackOpens: this._trackOpens,
      trackClicks: this._trackClicks,
      trackReplies: this._trackReplies,
      sendRateLimit: this._sendRateLimit,
      deliveryPriority: this._deliveryPriority,
      authenticationDomain: this._authenticationDomain,
      googleAnalytics: this._googleAnalytics,
      emailProvider: this._emailProvider,
      useCustomSmtp: this._useCustomSmtp,
      smtpSettings: this._smtpSettings ? {
        ...this._smtpSettings,
        password: '[REDACTED]', // Don't serialize SMTP password
      } : undefined,
      enableRetries: this._enableRetries,
      maxRetries: this._maxRetries,
      retryDelayMinutes: this._retryDelayMinutes,
      ipPool: this._ipPool,
      headers: this._headers,
      includeUnsubscribeLink: this._includeUnsubscribeLink,
      customUnsubscribeLink: this._customUnsubscribeLink,
      footer: this._footer,
      personalization: this._personalization,
      abTesting: this._abTesting,
    };
  }
}
