/*s self*
 * Mailgun Email Provider Implementation
 */
import axios, { AxiosInstance } from 'axios';
import FormData from 'form-data';
import {
  Email,
  EmailTemplate,
  SendResult,
  BulkSendResult,
  DeliveryStatus,
  Attachment
} from '../../domain/models';
import { EmailProvider } from '../../domain/interfaces';

/**
 * Implementation of EmailProvider for Mailgun
 */
export class MailgunEmailProvider implements EmailProvider {
  private readonly apiClient: AxiosInstance;
  readonly providerName = 'mailgun';

  /**
   * Creates a new MailgunEmailProvider instance
   * @param apiKey Mailgun API key
   * @param domain Mailgun domain
   * @param region Mailgun region (default: 'us')
   */
  constructor(
    private readonly apiKey: string,
    private readonly domain: string,
    private readonly region: 'us' | 'eu' = 'us'
  ) {
    const baseURL = region === 'eu'
      ? 'https://api.eu.mailgun.net/v3'
      : 'https://api.mailgun.net/v3';

    this.apiClient = axios.create({
      baseURL,
      auth: {
        username: 'api',
        password: apiKey
      }
    });
  }

  /**
   * Sends a single email through Mailgun
   * @param email The email to send
   * @returns Result of the send operation
   */
  async sendEmail(email: Email): Promise<SendResult> {
    try {
      const formData = this.formatEmailPayload(email);

      const response = await this.apiClient.post(
        `/${this.domain}/messages`,
        formData,
        {
          headers: formData.getHeaders()
        }
      );

      return {
        success: true,
        messageId: response.data.id,
        providerResponse: response.data,
        sentAt: new Date()
      };
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || 'Unknown error';

      return {
        success: false,
        error: `Mailgun error: ${errorMessage}`,
        sentAt: new Date()
      };
    }
  }

  /**
   * Sends multiple emails in bulk through Mailgun
   * @param emails Array of emails to send
   * @returns Result of the bulk send operation
   */
  async sendBulk(emails: Email[]): Promise<BulkSendResult> {
    try {
      // For small batches, use the batch endpoint
      if (emails.length <= 1000) {
        const recipientVariables: Record<string, any> = {};
        const baseEmail: Email = { ...emails[0] };

        // Extract common properties from the first email
        baseEmail.to = [];

        // Build recipient variables for mail merge
        emails.forEach((email, index) => {
          const to = Array.isArray(email.to) ? email.to[0] : email.to;
          (baseEmail.to as string[]).push(to);

          recipientVariables[to] = {
            index: index,
            ...email.templateVars
          };
        });

        // Create form data with recipient variables
        const formData = this.formatEmailPayload(baseEmail);
        formData.append('recipient-variables', JSON.stringify(recipientVariables));

        // Send batch email
        const response = await this.apiClient.post(
          `/${this.domain}/messages`,
          formData,
          {
            headers: formData.getHeaders()
          }
        );

        // Process results
        return {
          success: true,
          total: emails.length,
          sent: emails.length,
          failed: 0,
          results: emails.map((email, index) => ({
            success: true,
            messageId: `${response.data.id}_${index}`,
            to: Array.isArray(email.to) ? email.to[0] : email.to,
            sentAt: new Date()
          }))
        };
      } else {
        // For larger batches, send individually
        const results: (SendResult & { to: string })[] = [];
        let sent = 0;
        let failed = 0;

        for (const email of emails) {
          const result = await this.sendEmail(email);
          const to = Array.isArray(email.to) ? email.to[0] : email.to;

          results.push({
            ...result,
            to
          });

          if (result.success) {
            sent++;
          } else {
            failed++;
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
    } catch (error: any) {
      return {
        success: false,
        total: emails.length,
        sent: 0,
        failed: emails.length,
        results: emails.map(email => ({
          success: false,
          to: Array.isArray(email.to) ? email.to[0] : email.to,
          error: `Mailgun bulk error: ${error.message || 'Unknown error'}`,
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
      // Extract domain and message ID from the full message ID (domain/ID)
      const [domain, id] = messageId.includes('/')
        ? messageId.split('/')
        : [this.domain, messageId];

      const response = await this.apiClient.get(`/${domain}/events`, {
        params: {
          'message-id': id
        }
      });

      if (!response.data.items || response.data.items.length === 0) {
        return DeliveryStatus.UNKNOWN;
      }

      // Sort events by timestamp descending to get the latest status
      const events = response.data.items.sort((a: any, b: any) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      const latestEvent = events[0];
      const eventType = latestEvent.event;

      // Map Mailgun event types to our DeliveryStatus enum
      switch (eventType) {
        case 'accepted':
          return DeliveryStatus.PROCESSED;
        case 'delivered':
          return DeliveryStatus.DELIVERED;
        case 'failed':
          return DeliveryStatus.DROPPED;
        case 'rejected':
          return DeliveryStatus.REJECTED;
        case 'complained':
          return DeliveryStatus.COMPLAINED;
        case 'opened':
          return DeliveryStatus.OPENED;
        case 'clicked':
          return DeliveryStatus.CLICKED;
        case 'unsubscribed':
          return DeliveryStatus.UNSUBSCRIBED;
        case 'temporary-fail':
          return DeliveryStatus.DEFERRED;
        case 'permanent-fail':
          return DeliveryStatus.BOUNCED;
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
      const response = await this.apiClient.get(`/${this.domain}/templates/${templateId}`);

      const template: EmailTemplate = {
        id: response.data.template.name,
        name: response.data.template.name,
        subject: '',
        description: response.data.template.description || '',
        createdAt: new Date(response.data.template.createdAt * 1000),
        updatedAt: new Date(response.data.template.createdAt * 1000)
      };

      // Get the template version content
      const versionResponse = await this.apiClient.get(
        `/${this.domain}/templates/${templateId}/versions/${response.data.template.version.tag}`
      );

      template.html = versionResponse.data.template.version.template;
      template.version = versionResponse.data.template.version.tag;

      return template;
    } catch (error: any) {
      throw new Error(`Failed to get template: ${error.message}`);
    }
  }

  /**
   * Creates a template on Mailgun
   * @param template The template to create
   * @returns The created template
   */
  async createTemplate(template: Omit<EmailTemplate, 'id'>): Promise<EmailTemplate> {
    try {
      // Create the template
      const response = await this.apiClient.post(`/${this.domain}/templates`, {
        name: template.name,
        description: template.description || ''
      });

      const templateId = response.data.template.name;

      // Create template version
      const versionResponse = await this.apiClient.post(
        `/${this.domain}/templates/${templateId}/versions`,
        {
          template: template.html,
          tag: 'initial',
          active: 'yes'
        }
      );

      return {
        id: templateId,
        name: template.name,
        subject: template.subject,
        html: template.html,
        text: template.text,
        version: 'initial',
        description: template.description || '',
        createdAt: new Date(),
        updatedAt: new Date()
      };
    } catch (error: any) {
      throw new Error(`Failed to create template: ${error.message}`);
    }
  }

  /**
   * Updates a template on Mailgun
   * @param templateId The template ID
   * @param template The template data to update
   * @returns The updated template
   */
  async updateTemplate(templateId: string, template: Partial<EmailTemplate>): Promise<EmailTemplate> {
    try {
      // Update template info if name or description are provided
      if (template.name || template.description) {
        await this.apiClient.put(`/${this.domain}/templates/${templateId}`, {
          name: template.name,
          description: template.description
        });
      }

      // Update template content if provided
      if (template.html) {
        const versionTag = `v${Date.now()}`;

        // Create a new version
        await this.apiClient.post(
          `/${this.domain}/templates/${templateId}/versions`,
          {
            template: template.html,
            tag: versionTag,
            active: 'yes'
          }
        );
      }

      // Get the updated template
      return await this.getTemplate(templateId);
    } catch (error: any) {
      throw new Error(`Failed to update template: ${error.message}`);
    }
  }

  /**
   * Deletes a template from Mailgun
   * @param templateId The template ID to delete
   * @returns True if deletion was successful
   */
  async deleteTemplate(templateId: string): Promise<boolean> {
    try {
      await this.apiClient.delete(`/${this.domain}/templates/${templateId}`);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Formats an email for Mailgun's API
   * @param email The email to format
   * @returns FormData object for Mailgun API
   */
  private formatEmailPayload(email: Email): FormData {
    const formData = new FormData();

    // From
    formData.append('from', email.from);

    // To (can be multiple)
    if (Array.isArray(email.to)) {
      email.to.forEach(to => formData.append('to', to));
    } else {
      formData.append('to', email.to);
    }

    // Subject
    formData.append('subject', email.subject);

    // Email content
    if (email.html) {
      formData.append('html', email.html);
    }

    if (email.text) {
      formData.append('text', email.text);
    }

    // CC (can be multiple)
    if (email.cc) {
      if (Array.isArray(email.cc)) {
        email.cc.forEach(cc => formData.append('cc', cc));
      } else {
        formData.append('cc', email.cc);
      }
    }

    // BCC (can be multiple)
    if (email.bcc) {
      if (Array.isArray(email.bcc)) {
        email.bcc.forEach(bcc => formData.append('bcc', bcc));
      } else {
        formData.append('bcc', email.bcc);
      }
    }

    // Reply-To
    if (email.replyTo) {
      formData.append('h:Reply-To', email.replyTo);
    }

    // Template and template variables
    if (email.templateId) {
      formData.append('template', email.templateId);

      if (email.templateVars) {
        // Add template variables as 'v:' prefixed form fields
        Object.entries(email.templateVars).forEach(([key, value]) => {
          formData.append(`v:${key}`, typeof value === 'object' ? JSON.stringify(value) : String(value));
        });
      }
    }

    // Headers (custom headers need h: prefix)
    if (email.headers) {
      Object.entries(email.headers).forEach(([key, value]) => {
        formData.append(`h:${key}`, value);
      });
    }

    // Attachments
    if (email.attachments && email.attachments.length > 0) {
      email.attachments.forEach((attachment, index) => {
        // For inline attachments
        if (attachment.disposition === 'inline' && attachment.contentId) {
          formData.append('inline', attachment.content, {
            filename: attachment.filename,
            contentType: attachment.contentType
          });
        } else {
          // Regular attachments
          formData.append('attachment', attachment.content, {
            filename: attachment.filename,
            contentType: attachment.contentType
          });
        }
      });
    }

    // Tags (can be multiple)
    if (email.tags) {
      email.tags.forEach(tag => formData.append('o:tag', tag));
    }

    // Tracking options
    if (email.tracking) {
      if (email.tracking.opens !== undefined) {
        formData.append('o:tracking-opens', email.tracking.opens ? 'yes' : 'no');
      }

      if (email.tracking.clicks !== undefined) {
        formData.append('o:tracking-clicks', email.tracking.clicks ? 'yes' : 'no');
      }
    }

    // Delivery time options (future sending) could be added here

    // Message metadata
    if (email.metadata) {
      Object.entries(email.metadata).forEach(([key, value]) => {
        formData.append(`v:${key}`, typeof value === 'object' ? JSON.stringify(value) : String(value));
      });
    }

    return formData;
  }
}
