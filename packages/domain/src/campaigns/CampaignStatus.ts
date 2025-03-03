/**
 * Represents the status of a campaign in its lifecycle.
 */
export enum CampaignStatus {
  /**
   * Initial state when the campaign is being created and edited
   */
  DRAFT = 'DRAFT',
  
  /**
   * The campaign has been scheduled to be sent at a future date
   */
  SCHEDULED = 'SCHEDULED',
  
  /**
   * The campaign is currently being sent
   */
  SENDING = 'SENDING',
  
  /**
   * The campaign has been successfully sent to all recipients
   */
  SENT = 'SENT',
  
  /**
   * The campaign has been cancelled before it was fully sent
   */
  CANCELLED = 'CANCELLED',
  
  /**
   * The campaign failed during sending
   */
  FAILED = 'FAILED'
}