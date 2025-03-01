/**
 * Domain service interfaces
 */
import { Email, EmailTemplate, SendResult, BulkSendResult, DeliveryStatus } from './models';

/**
 * Interface for email sending services
 */
export interface EmailSender {
  /**
   * Sends a single email
   * @param email The email to send
   * @returns Result of the send operation
   */
  sendEmail(email: Email): Promise<SendResult>;

  /**
   * Sends multiple emails in bulk
   * @param emails Array of emails to send
   * @returns Result of the bulk send operation
   */
  sendBulk(emails: Email[]): Promise<BulkSendResult>;

  /**
   * Gets the current delivery status of an email
   * @param messageId The message ID to check
   * @returns Current delivery status
   */
  getDeliveryStatus(messageId: string): Promise<DeliveryStatus>;
}

/**
 * Interface for email template services
 */
export interface EmailTemplateService {
  /**
   * Gets a template by ID
   * @param templateId The template ID
   * @returns The email template
   */
  getTemplate(templateId: string): Promise<EmailTemplate>;

  /**
   * Creates a new template
   * @param template The template to create
   * @returns The created template
   */
  createTemplate(template: Omit<EmailTemplate, 'id'>): Promise<EmailTemplate>;

  /**
   * Updates an existing template
   * @param templateId The template ID
   * @param template The template data to update
   * @returns The updated template
   */
  updateTemplate(templateId: string, template: Partial<EmailTemplate>): Promise<EmailTemplate>;

  /**
   * Deletes a template
   * @param templateId The template ID to delete
   * @returns True if deletion was successful
   */
  deleteTemplate(templateId: string): Promise<boolean>;

  /**
   * Renders a template with variables
   * @param templateId The template ID
   * @param variables The variables to render with
   * @returns The rendered template content
   */
  renderTemplate(templateId: string, variables: Record<string, any>): Promise<{ html?: string; text?: string }>;
}

/**
 * Interface for email storage repositories
 */
export interface EmailRepository {
  /**
   * Saves an email record
   * @param email The email to save
   * @returns The saved email with ID
   */
  saveEmail(email: Email): Promise<Email>;

  /**
   * Gets an email by ID
   * @param emailId The email ID
   * @returns The email if found
   */
  getEmailById(emailId: string): Promise<Email | null>;

  /**
   * Updates email delivery status
   * @param emailId The email ID
   * @param status The new delivery status
   * @returns True if update was successful
   */
  updateDeliveryStatus(emailId: string, status: DeliveryStatus): Promise<boolean>;

  /**
   * Queries emails by filter criteria
   * @param filter The filter criteria
   * @param page Pagination page number
   * @param pageSize Page size for pagination
   * @returns Paginated list of emails
   */
  queryEmails(filter: Record<string, any>, page: number, pageSize: number): Promise<{ emails: Email[]; total: number }>;
}

/**
 * Interface for email provider adapters
 */
export interface EmailProvider {
  /**
   * Provider name identifier
   */
  readonly providerName: string;

  /**
   * Sends a single email
   * @param email The email to send
   * @returns Result of the send operation
   */
  sendEmail(email: Email): Promise<SendResult>;

  /**
   * Sends multiple emails in bulk
   * @param emails Array of emails to send
   * @returns Result of the bulk send operation
   */
  sendBulk(emails: Email[]): Promise<BulkSendResult>;

  /**
   * Gets the current delivery status of an email
   * @param messageId The message ID to check
   * @returns Current delivery status
   */
  getDeliveryStatus(messageId: string): Promise<DeliveryStatus>;

  /**
   * Gets a template by ID
   * @param templateId The template ID
   * @returns The email template
   */
  getTemplate(templateId: string): Promise<EmailTemplate>;

  /**
   * Creates a template on the provider
   * @param template The template to create
   * @returns The created template
   */
  createTemplate(template: Omit<EmailTemplate, 'id'>): Promise<EmailTemplate>;

  /**
   * Updates a template on the provider
   * @param templateId The template ID
   * @param template The template data to update
   * @returns The updated template
   */
  updateTemplate(templateId: string, template: Partial<EmailTemplate>): Promise<EmailTemplate>;

  /**
   * Deletes a template from the provider
   * @param templateId The template ID to delete
   * @returns True if deletion was successful
   */
  deleteTemplate(templateId: string): Promise<boolean>;
}
