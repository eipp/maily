/**
 * Email service use cases
 */
import {
  Email,
  EmailTemplate,
  SendResult,
  BulkSendResult,
  DeliveryStatus
} from '../../domain/models';
import {
  EmailSender,
  EmailTemplateService,
  EmailRepository,
  EmailProvider
} from '../../domain/interfaces';

/**
 * Email service implementation
 */
export class EmailService implements EmailSender, EmailTemplateService {
  private emailProvider: EmailProvider;
  private emailRepository: EmailRepository;
  private metricsService: EmailMetricsService;
  private rateLimiter: EmailRateLimiter;

  /**
   * Creates a new EmailService instance
   */
  constructor(
    emailProvider: EmailProvider,
    emailRepository: EmailRepository,
    metricsService: EmailMetricsService,
    rateLimiter: EmailRateLimiter
  ) {
    this.emailProvider = emailProvider;
    this.emailRepository = emailRepository;
    this.metricsService = metricsService;
    this.rateLimiter = rateLimiter;
  }

  /**
   * Sends a single email
   * @param email The email to send
   * @returns Result of the send operation
   */
  async sendEmail(email: Email): Promise<SendResult> {
    try {
      // Save email to repository before sending
      const savedEmail = await this.emailRepository.saveEmail(email);

      // Start timing the send operation
      const startTime = Date.now();

      // Send the email through the provider
      const result = await this.emailProvider.sendEmail(savedEmail);

      // Calculate duration and record metrics
      const duration = Date.now() - startTime;
      this.metricsService.recordSendDuration(
        this.emailProvider.providerName,
        duration
      );

      // Record success/failure metrics
      this.metricsService.recordSend(
        this.emailProvider.providerName,
        email.templateId || 'custom',
        result.success ? 'success' : 'failure'
      );

      // Update delivery status in repository
      if (result.success && result.messageId) {
        await this.emailRepository.updateDeliveryStatus(
          savedEmail.id!,
          DeliveryStatus.SENT
        );
      }

      return result;
    } catch (error: any) {
      // Record provider error
      this.metricsService.recordProviderError(
        this.emailProvider.providerName,
        error.name || 'UnknownError'
      );

      return {
        success: false,
        error: error.message || 'Unknown error occurred',
        sentAt: new Date()
      };
    }
  }

  /**
   * Sends multiple emails in bulk
   * @param emails Array of emails to send
   * @returns Result of the bulk send operation
   */
  async sendBulk(emails: Email[]): Promise<BulkSendResult> {
    try {
      // Save all emails to repository before sending
      const savedEmails = await Promise.all(
        emails.map(email => this.emailRepository.saveEmail(email))
      );

      // Start timing the bulk send operation
      const startTime = Date.now();

      // Send emails in bulk through the provider
      const result = await this.emailProvider.sendBulk(savedEmails);

      // Calculate duration and record metrics
      const duration = Date.now() - startTime;
      this.metricsService.recordSendDuration(
        this.emailProvider.providerName,
        duration
      );

      // Record success/failure metrics for each email
      result.results.forEach(individualResult => {
        this.metricsService.recordSend(
          this.emailProvider.providerName,
          emails.find(e => e.to === individualResult.to)?.templateId || 'custom',
          individualResult.success ? 'success' : 'failure'
        );
      });

      // Update delivery status for each successful email
      await Promise.all(
        result.results
          .filter(r => r.success && r.messageId)
          .map(r => {
            const email = savedEmails.find(e =>
              Array.isArray(e.to)
                ? e.to.includes(r.to)
                : e.to === r.to
            );

            if (email && email.id) {
              return this.emailRepository.updateDeliveryStatus(
                email.id,
                DeliveryStatus.SENT
              );
            }
            return Promise.resolve(false);
          })
      );

      return result;
    } catch (error: any) {
      // Record provider error
      this.metricsService.recordProviderError(
        this.emailProvider.providerName,
        error.name || 'UnknownError'
      );

      return {
        success: false,
        total: emails.length,
        sent: 0,
        failed: emails.length,
        results: emails.map(email => ({
          success: false,
          to: Array.isArray(email.to) ? email.to[0] : email.to,
          error: error.message || 'Unknown error occurred',
          sentAt: new Date()
        }))
      };
    }
  }

  /**
   * Gets the current delivery status of an email
   * @param messageId The message ID to check
   * @returns Current delivery status
   */
  async getDeliveryStatus(messageId: string): Promise<DeliveryStatus> {
    try {
      // Get status from the provider
      const status = await this.emailProvider.getDeliveryStatus(messageId);

      // Record delivery status metric
      this.metricsService.recordDelivery(
        this.emailProvider.providerName,
        status
      );

      return status;
    } catch (error: any) {
      // Record provider error
      this.metricsService.recordProviderError(
        this.emailProvider.providerName,
        error.name || 'UnknownError'
      );

      return DeliveryStatus.UNKNOWN;
    }
  }

  /**
   * Gets a template by ID
   * @param templateId The template ID
   * @returns The email template
   */
  async getTemplate(templateId: string): Promise<EmailTemplate> {
    return this.emailProvider.getTemplate(templateId);
  }

  /**
   * Creates a new template
   * @param template The template to create
   * @returns The created template
   */
  async createTemplate(template: Omit<EmailTemplate, 'id'>): Promise<EmailTemplate> {
    return this.emailProvider.createTemplate(template);
  }

  /**
   * Updates an existing template
   * @param templateId The template ID
   * @param template The template data to update
   * @returns The updated template
   */
  async updateTemplate(templateId: string, template: Partial<EmailTemplate>): Promise<EmailTemplate> {
    return this.emailProvider.updateTemplate(templateId, template);
  }

  /**
   * Deletes a template
   * @param templateId The template ID to delete
   * @returns True if deletion was successful
   */
  async deleteTemplate(templateId: string): Promise<boolean> {
    return this.emailProvider.deleteTemplate(templateId);
  }

  /**
   * Renders a template with variables
   * @param templateId The template ID
   * @param variables The variables to render with
   * @returns The rendered template content
   */
  async renderTemplate(
    templateId: string,
    variables: Record<string, any>
  ): Promise<{ html?: string; text?: string }> {
    // Get the template first
    const template = await this.getTemplate(templateId);

    // For providers that don't handle rendering directly, we'd need
    // to implement our own template rendering logic here
    // This is a simplified placeholder that assumes the provider
    // handles rendering via API

    const html = template.html ? this.renderVariables(template.html, variables) : undefined;
    const text = template.text ? this.renderVariables(template.text, variables) : undefined;

    return { html, text };
  }

  /**
   * Simple variable rendering helper (placeholder)
   * In a real implementation, use a proper template engine
   */
  private renderVariables(content: string, variables: Record<string, any>): string {
    let rendered = content;
    for (const [key, value] of Object.entries(variables)) {
      const regex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
      rendered = rendered.replace(regex, String(value));
    }
    return rendered;
  }
}

/**
 * Interface for email metrics service
 */
export interface EmailMetricsService {
  recordSend(provider: string, template: string, status: string): void;
  recordSendDuration(provider: string, durationMs: number): void;
  recordDelivery(provider: string, status: string): void;
  recordProviderError(provider: string, errorType: string): void;
}

/**
 * Interface for email rate limiter
 */
export interface EmailRateLimiter {
  allowSend(provider: string, userId: string): Promise<boolean>;
}
