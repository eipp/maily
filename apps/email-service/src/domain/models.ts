/**
 * Email domain models
 */

export interface Email {
  /** Unique identifier for the email */
  id?: string;
  /** Sender email address */
  from: string;
  /** Recipient email address */
  to: string | string[];
  /** Email subject */
  subject: string;
  /** Email content in HTML format */
  html?: string;
  /** Email content in text format */
  text?: string;
  /** Carbon copy recipients */
  cc?: string | string[];
  /** Blind carbon copy recipients */
  bcc?: string | string[];
  /** Reply-to email address */
  replyTo?: string;
  /** Email headers */
  headers?: Record<string, string>;
  /** Attachments */
  attachments?: Attachment[];
  /** Template ID if using a template */
  templateId?: string;
  /** Template variables */
  templateVars?: Record<string, any>;
  /** Tracking options */
  tracking?: {
    opens?: boolean;
    clicks?: boolean;
    unsubscribe?: boolean;
  };
  /** Metadata for tracking and analytics */
  metadata?: Record<string, any>;
  /** Tags for categorization */
  tags?: string[];
  /** Priority level */
  priority?: 'high' | 'normal' | 'low';
}

export interface Attachment {
  /** Filename of the attachment */
  filename: string;
  /** Content of the attachment */
  content: Buffer | string;
  /** MIME type of the attachment */
  contentType?: string;
  /** Content ID for inline attachments */
  contentId?: string;
  /** Disposition of the attachment (inline or attachment) */
  disposition?: 'inline' | 'attachment';
}

export interface EmailTemplate {
  /** Unique identifier for the template */
  id: string;
  /** Template name */
  name: string;
  /** Template subject */
  subject: string;
  /** Template content in HTML format */
  html?: string;
  /** Template content in text format */
  text?: string;
  /** Template version */
  version?: string;
  /** Template variables */
  variables?: string[];
  /** Template description */
  description?: string;
  /** Template created date */
  createdAt?: Date;
  /** Template updated date */
  updatedAt?: Date;
}

export type SendResult = {
  /** Success status of the send operation */
  success: boolean;
  /** Message ID from the provider */
  messageId?: string;
  /** Error message if send failed */
  error?: string;
  /** Provider-specific response */
  providerResponse?: any;
  /** Timestamp when the email was sent */
  sentAt: Date;
  /** Indicates if the circuit breaker prevented the request */
  circuitBroken?: boolean;
  /** Categorized error type for better handling */
  errorCategory?: 'rate_limit' | 'authentication' | 'validation' | 'server' | 'network' | 'unknown';
  /** Error code from the provider */
  errorCode?: string;
  /** HTTP status code from the provider */
  statusCode?: number;
};

export type BulkSendResult = {
  /** Overall success status of the bulk send operation */
  success: boolean;
  /** Total number of emails in the request */
  total: number;
  /** Number of successfully sent emails */
  sent: number;
  /** Number of failed emails */
  failed: number;
  /** Results for each individual email */
  results: (SendResult & { to: string })[];
};

export enum DeliveryStatus {
  SENT = 'sent',
  DELIVERED = 'delivered',
  DEFERRED = 'deferred',
  BOUNCED = 'bounced',
  REJECTED = 'rejected',
  COMPLAINED = 'complained',
  OPENED = 'opened',
  CLICKED = 'clicked',
  UNSUBSCRIBED = 'unsubscribed',
  PROCESSED = 'processed',
  DROPPED = 'dropped',
  UNKNOWN = 'unknown'
}
