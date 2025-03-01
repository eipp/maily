/**
 * Resend Email Provider Implementation
 */
import axios, { AxiosInstance } from 'axios';
import {
  Email,
  EmailTemplate,
  SendResult,
  BulkSendResult,
  DeliveryStatus
} from '../../domain/models';
import { EmailProvider } from '../../domain/interfaces';

/**
 * Implementation of EmailProvider for Resend
 */
export class ResendEmailProvider implements EmailProvider {
  private readonly apiClient: AxiosInstance;
  readonly providerName = 'resend';

  // Circuit breaker properties
  private circuitState: 'closed' | 'open' | 'half-open' = 'closed';
  private failureCount = 0;
  private failureThreshold = 5;
  private resetTimeout = 30000; // 30 seconds
  private lastFailureTime = 0;
  private resetTimer: NodeJS.Timeout | null = null;

  /**
   * Creates a new ResendEmailProvider instance
   * @param apiKey Resend API key
   * @param circuitConfig Optional circuit breaker configuration
   */
  constructor(
    protected readonly apiKey: string,
    protected readonly circuitConfig: {
      failureThreshold?: number;
      resetTimeout?: number;
    } = {}
  ) {
    this.apiClient = axios.create({
      baseURL: 'https://api.resend.com',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    // Apply custom circuit breaker config if provided
    if (circuitConfig.failureThreshold) {
      this.failureThreshold = circuitConfig.failureThreshold;
    }

    if (circuitConfig.resetTimeout) {
      this.resetTimeout = circuitConfig.resetTimeout;
    }
  }

  /**
   * Checks circuit state to determine if requests should be allowed
   * @returns true if requests are allowed, false otherwise
   */
  private checkCircuitState(): boolean {
    if (this.circuitState === 'closed') {
      return true; // Allow requests when circuit is closed
    }

    if (this.circuitState === 'open') {
      // Check if it's time to try half-open state
      const now = Date.now();
      if (now - this.lastFailureTime >= this.resetTimeout) {
        console.log('Circuit transitioning from open to half-open state');
        this.circuitState = 'half-open';
        return true; // Allow a test request
      }
      return false; // Reject requests when circuit is open
    }

    // For half-open state, we allow the request to test if the service is healthy
    return true;
  }

  /**
   * Records a successful operation for circuit breaker
   */
  private recordSuccess(): void {
    if (this.circuitState === 'half-open') {
      console.log('Circuit transitioning from half-open to closed state');
      this.circuitState = 'closed';
      this.failureCount = 0;
      if (this.resetTimer) {
        clearTimeout(this.resetTimer);
        this.resetTimer = null;
      }
    }
  }

  /**
   * Records a failure operation for circuit breaker
   */
  private recordFailure(): void {
    this.lastFailureTime = Date.now();

    if (this.circuitState === 'half-open') {
      console.log('Circuit transitioning from half-open back to open state');
      this.circuitState = 'open';

      // Schedule reset to half-open
      if (this.resetTimer) {
        clearTimeout(this.resetTimer);
      }
      this.resetTimer = setTimeout(() => {
        if (this.circuitState === 'open') {
          console.log('Circuit timeout elapsed, transitioning to half-open state');
          this.circuitState = 'half-open';
        }
      }, this.resetTimeout);

      return;
    }

    if (this.circuitState === 'closed') {
      this.failureCount++;

      if (this.failureCount >= this.failureThreshold) {
        console.log(`Circuit reached failure threshold (${this.failureThreshold}), transitioning to open state`);
        this.circuitState = 'open';

        // Schedule reset to half-open
        if (this.resetTimer) {
          clearTimeout(this.resetTimer);
        }
        this.resetTimer = setTimeout(() => {
          if (this.circuitState === 'open') {
            console.log('Circuit timeout elapsed, transitioning to half-open state');
            this.circuitState = 'half-open';
          }
        }, this.resetTimeout);
      }
    }
  }

  /**
   * Sends a single email through Resend
   * @param email The email to send
   * @returns Result of the send operation
   */
  async sendEmail(email: Email): Promise<SendResult> {
    // Check if circuit is open
    if (!this.checkCircuitState()) {
      return {
        success: false,
        error: 'Circuit breaker open: Too many recent failures',
        circuitBroken: true,
        sentAt: new Date()
      };
    }

    try {
      const payload = this.formatEmailPayload(email);

      const response = await this.apiClient.post('/emails', payload);

      // Record success for circuit breaker
      this.recordSuccess();

      return {
        success: true,
        messageId: response.data.id,
        providerResponse: response.data,
        sentAt: new Date()
      };
    } catch (error: any) {
      // Record failure for circuit breaker
      this.recordFailure();

      // Extract detailed error information
      const statusCode = error.response?.status;
      const errorResponse = error.response?.data;
      const errorCode = errorResponse?.code || errorResponse?.error?.code;
      const errorMessage = errorResponse?.message || errorResponse?.error?.message || error.message || 'Unknown error';

      // Log error with context for monitoring
      console.error(`Resend API error (${statusCode}): ${errorMessage}`, {
        code: errorCode,
        statusCode,
        errorResponse,
        timestamp: new Date().toISOString()
      });

      // Determine error category for better handling
      let errorCategory: 'rate_limit' | 'authentication' | 'validation' | 'server' | 'network' | 'unknown' = 'unknown';

      if (statusCode === 429 || errorMessage.includes('rate') || errorMessage.includes('limit')) {
        errorCategory = 'rate_limit';
      } else if (statusCode === 401 || statusCode === 403 || errorMessage.includes('auth') || errorMessage.includes('key')) {
        errorCategory = 'authentication';
      } else if (statusCode === 400 || errorMessage.includes('valid')) {
        errorCategory = 'validation';
      } else if (statusCode && statusCode >= 500) {
        errorCategory = 'server';
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT' || !statusCode) {
        errorCategory = 'network';
      }

      return {
        success: false,
        error: `Resend error: ${errorMessage}`,
        errorCategory,
        errorCode,
        statusCode,
        sentAt: new Date()
      };
    }
  }

  /**
   * Sends multiple emails in bulk through Resend using concurrent batches
   * @param emails Array of emails to send
   * @param batchSize Optional batch size (default: 25)
   * @returns Result of the bulk send operation
   */
  async sendBulk(emails: Email[], batchSize: number = 25): Promise<BulkSendResult> {
    const results: (SendResult & { to: string })[] = [];
    let sent = 0;
    let failed = 0;

    // Process emails in batches
    for (let i = 0; i < emails.length; i += batchSize) {
      const batch = emails.slice(i, i + batchSize);

      try {
        // Send batch concurrently
        const batchPromises = batch.map(async (email) => {
          try {
            const result = await this.sendEmail(email);
            const to = Array.isArray(email.to) ? email.to[0] : email.to;

            return {
              ...result,
              to
            };
          } catch (error: any) {
            // Handle individual email errors without failing the entire batch
            const errorMessage = error.response?.data?.message || error.message || 'Unknown error';

            return {
              success: false,
              error: `Resend error: ${errorMessage}`,
              sentAt: new Date(),
              to: Array.isArray(email.to) ? email.to[0] : email.to
            };
          }
        });

        // Wait for all emails in this batch to complete
        const batchResults = await Promise.all(batchPromises);

        // Process batch results
        for (const result of batchResults) {
          results.push(result);

          if (result.success) {
            sent++;
          } else {
            failed++;
          }
        }

        // Add a small delay between batches to avoid rate limiting
        if (i + batchSize < emails.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      } catch (error: any) {
        // This should only happen if there's a catastrophic error with the entire batch
        console.error(`Batch send error at offset ${i}:`, error);

        // Mark all emails in this batch as failed
        for (const email of batch) {
          const to = Array.isArray(email.to) ? email.to[0] : email.to;
          const errorMessage = error.response?.data?.message || error.message || 'Unknown error';

          results.push({
            success: false,
            error: `Batch processing error: ${errorMessage}`,
            sentAt: new Date(),
            to
          });

          failed += batch.length;
        }
      }
    }

    return {
      success: failed === 0,
      total: emails.length,
      sent,
      failed,
      results
    };
  }

  /**
   * Gets the current delivery status of an email
   * @param messageId The message ID to check
   * @returns Current delivery status
   */
  async getDeliveryStatus(messageId: string): Promise<DeliveryStatus> {
    try {
      const response = await this.apiClient.get(`/emails/${messageId}`);

      const status = response.data.status;

      // Map Resend status to our DeliveryStatus enum
      switch (status) {
        case 'sent':
          return DeliveryStatus.SENT;
        case 'delivered':
          return DeliveryStatus.DELIVERED;
        case 'delivery_delayed':
          return DeliveryStatus.DEFERRED;
        case 'bounce':
          return DeliveryStatus.BOUNCED;
        case 'complaint':
          return DeliveryStatus.COMPLAINED;
        case 'open':
          return DeliveryStatus.OPENED;
        case 'click':
          return DeliveryStatus.CLICKED;
        case 'blocked':
          return DeliveryStatus.REJECTED;
        case 'failed':
          return DeliveryStatus.DROPPED;
        default:
          return DeliveryStatus.UNKNOWN;
      }
    } catch (error) {
      return DeliveryStatus.UNKNOWN;
    }
  }

  /**
   * Gets a template by ID
   * @param templateId The template ID
   * @returns The email template
   */
  async getTemplate(templateId: string): Promise<EmailTemplate> {
    try {
      const response = await this.apiClient.get(`/templates/${templateId}`);

      return {
        id: response.data.id,
        name: response.data.name,
        subject: response.data.subject || '',
        html: response.data.html,
        text: response.data.text,
        version: response.data.version,
        variables: response.data.variables || [],
        description: response.data.description || '',
        createdAt: new Date(response.data.created_at),
        updatedAt: new Date(response.data.updated_at)
      };
    } catch (error: any) {
      throw new Error(`Failed to get template: ${error.message}`);
    }
  }

  /**
   * Creates a template on Resend
   * @param template The template to create
   * @returns The created template
   */
  async createTemplate(template: Omit<EmailTemplate, 'id'>): Promise<EmailTemplate> {
    try {
      const response = await this.apiClient.post('/templates', {
        name: template.name,
        html: template.html,
        text: template.text,
        subject: template.subject,
        description: template.description
      });

      return {
        id: response.data.id,
        name: response.data.name,
        subject: response.data.subject || '',
        html: response.data.html,
        text: response.data.text,
        version: response.data.version,
        variables: response.data.variables || [],
        description: response.data.description || '',
        createdAt: new Date(response.data.created_at),
        updatedAt: new Date(response.data.updated_at)
      };
    } catch (error: any) {
      throw new Error(`Failed to create template: ${error.message}`);
    }
  }

  /**
   * Updates a template on Resend
   * @param templateId The template ID
   * @param template The template data to update
   * @returns The updated template
   */
  async updateTemplate(templateId: string, template: Partial<EmailTemplate>): Promise<EmailTemplate> {
    try {
      const response = await this.apiClient.patch(`/templates/${templateId}`, {
        name: template.name,
        html: template.html,
        text: template.text,
        subject: template.subject,
        description: template.description
      });

      return {
        id: response.data.id,
        name: response.data.name,
        subject: response.data.subject || '',
        html: response.data.html,
        text: response.data.text,
        version: response.data.version,
        variables: response.data.variables || [],
        description: response.data.description || '',
        createdAt: new Date(response.data.created_at),
        updatedAt: new Date(response.data.updated_at)
      };
    } catch (error: any) {
      throw new Error(`Failed to update template: ${error.message}`);
    }
  }

  /**
   * Deletes a template from Resend
   * @param templateId The template ID to delete
   * @returns True if deletion was successful
   */
  async deleteTemplate(templateId: string): Promise<boolean> {
    try {
      await this.apiClient.delete(`/templates/${templateId}`);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Formats an email for Resend's API
   * @param email The email to format
   * @returns Formatted email payload for Resend
   */
  private formatEmailPayload(email: Email): any {
    const payload: any = {
      from: email.from,
      subject: email.subject
    };

    // Handle single recipient or multiple recipients
    if (Array.isArray(email.to)) {
      payload.to = email.to;
    } else {
      payload.to = [email.to];
    }

    // Add optional fields if they exist
    if (email.html) {
      payload.html = email.html;
    }

    if (email.text) {
      payload.text = email.text;
    }

    if (email.cc) {
      payload.cc = Array.isArray(email.cc) ? email.cc : [email.cc];
    }

    if (email.bcc) {
      payload.bcc = Array.isArray(email.bcc) ? email.bcc : [email.bcc];
    }

    if (email.replyTo) {
      payload.reply_to = email.replyTo;
    }

    if (email.attachments && email.attachments.length > 0) {
      payload.attachments = email.attachments.map(attachment => ({
        filename: attachment.filename,
        content: attachment.content,
        content_type: attachment.contentType,
        content_id: attachment.contentId,
        disposition: attachment.disposition
      }));
    }

    if (email.headers) {
      payload.headers = email.headers;
    }

    if (email.tags) {
      payload.tags = email.tags.map(tag => ({ name: tag }));
    }

    return payload;
  }
}
