/**
 * Domain enumerations
 */

/**
 * Campaign status
 */
export enum CampaignStatus {
  /**
   * Initial state, being edited
   */
  DRAFT = 'draft',

  /**
   * Ready for delivery at scheduled time
   */
  SCHEDULED = 'scheduled',

  /**
   * Currently being sent
   */
  SENDING = 'sending',

  /**
   * Temporarily stopped sending
   */
  PAUSED = 'paused',

  /**
   * All emails sent
   */
  COMPLETED = 'completed',

  /**
   * Manually stopped before completion
   */
  CANCELED = 'canceled',

  /**
   * Failed due to error
   */
  FAILED = 'failed',
}

/**
 * Campaign type
 */
export enum CampaignType {
  /**
   * Regular marketing campaign
   */
  MARKETING = 'marketing',

  /**
   * Transactional emails
   */
  TRANSACTIONAL = 'transactional',

  /**
   * Automated based on user behavior
   */
  AUTOMATED = 'automated',

  /**
   * A/B testing campaign
   */
  AB_TEST = 'ab_test',

  /**
   * Re-engagement campaign
   */
  RE_ENGAGEMENT = 're_engagement',

  /**
   * Onboarding sequence
   */
  ONBOARDING = 'onboarding',

  /**
   * Newsletter
   */
  NEWSLETTER = 'newsletter',
}

/**
 * Email delivery status
 */
export enum EmailDeliveryStatus {
  /**
   * Waiting to be sent
   */
  PENDING = 'pending',

  /**
   * Successfully delivered to recipient's server
   */
  DELIVERED = 'delivered',

  /**
   * Opened by recipient
   */
  OPENED = 'opened',

  /**
   * Clicked by recipient
   */
  CLICKED = 'clicked',

  /**
   * Recipient unsubscribed
   */
  UNSUBSCRIBED = 'unsubscribed',

  /**
   * Bounced (not delivered)
   */
  BOUNCED = 'bounced',

  /**
   * Recipient marked as spam
   */
  COMPLAINED = 'complained',

  /**
   * Failed to send
   */
  FAILED = 'failed',
}

/**
 * Recipient status
 */
export enum RecipientStatus {
  /**
   * Active and can receive emails
   */
  ACTIVE = 'active',

  /**
   * Has unsubscribed
   */
  UNSUBSCRIBED = 'unsubscribed',

  /**
   * Bounced previously
   */
  BOUNCED = 'bounced',

  /**
   * Reported spam
   */
  COMPLAINED = 'complained',

  /**
   * Suppressed by the system
   */
  SUPPRESSED = 'suppressed',
}

/**
 * Template content type
 */
export enum TemplateContentType {
  /**
   * HTML content
   */
  HTML = 'html',

  /**
   * Plain text content
   */
  TEXT = 'text',

  /**
   * Markdown content
   */
  MARKDOWN = 'markdown',

  /**
   * MJML framework
   */
  MJML = 'mjml',

  /**
   * React JSX components
   */
  REACT = 'react',
}

/**
 * Audience type
 */
export enum AudienceType {
  /**
   * Static list of recipients
   */
  STATIC = 'static',

  /**
   * Dynamic segment based on criteria
   */
  SEGMENT = 'segment',

  /**
   * Imported from external source
   */
  IMPORTED = 'imported',

  /**
   * Computed by behavior or attributes
   */
  DYNAMIC = 'dynamic',
}

/**
 * Schedule type
 */
export enum ScheduleType {
  /**
   * Send immediately
   */
  IMMEDIATE = 'immediate',

  /**
   * Send at specific date/time
   */
  SCHEDULED = 'scheduled',

  /**
   * Send at optimal time for each recipient
   */
  OPTIMAL_TIME = 'optimal_time',

  /**
   * Recurring schedule
   */
  RECURRING = 'recurring',
}
