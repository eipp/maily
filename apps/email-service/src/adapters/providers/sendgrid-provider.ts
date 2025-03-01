 /**
 * SendGrid Email Provider Implementation
 */
import axios, { AxiosInstance } from 'axios';
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
 * Implementation of EmailProvider for SendGrid
 */
export class SendGridEmailProvider implements EmailProvider {
  private readonly apiClient: AxiosInstance;
  readonly providerName = 'sendgrid';

  /**
   * Creates a new SendGridEmailProvider instance
   * @param apiKey SendGrid API key
   */
  constructor(private readonly apiKey: string) {
    this.apiClient = axios.create({
      baseURL: 'https://api.sendgrid.com/v3',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  /**
   * Sends a single email through SendGrid
   * @param email The email to send
   * @returns Result of the send operation
   */
  async sendEmail(email: Email): Promise<SendResult> {
    try {
      const payload = this.formatEmailPayload(email);

      const response = await this.apiClient.post('/mail/send', payload);

      // SendGrid doesn't return a message ID in the response
      // We need to extract it from headers or use a UUID
      const messageId = response.headers['x-message-id'] ||
                         this.generateMessageId(email);

      return {
        success: true,
        messageId,
        providerResponse: response.data,
        sentAt: new Date()
      };
    } catch (error: any) {
      const errorMessage = error.response?.data?.errors?.[0]?.message ||
                          error.message ||
                          'Unknown error';

      return {
        success: false,
        error: `SendGrid error: ${errorMessage}`,
        sentAt: new Date()
      };
    }
  }

  /**
   * Sends multiple emails in bulk through SendGrid
   * @param emails Array of emails to send
   * @returns Result of the bulk send operation
   */
  async sendBulk(emails: Email[]): Promise<BulkSendResult> {
    try {
      // SendGrid allows for bulk sending with personalization
      // We need to decide if we send as single API call with personalizations
      // or multiple calls for more flexibility

      // For simplicity and flexibility, we'll use multiple API calls
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
    } catch (error: any) {
      return {
        success: false,
        total: emails.length,
        sent: 0,
        failed: emails.length,
        results: emails.map(email => ({
          success: false,
          to: Array.isArray(email.to) ? email.to[0] : email.to,
          error: `SendGrid bulk error: ${error.message || 'Unknown error'}`,
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
      // SendGrid doesn't have a direct API to get status by message ID
      // We need to query events with the message ID filter
      const response = await this.apiClient.get('/messages', {
        params: {
          'query': `msg_id="${messageId}"`,
          'limit': 1
        }
      });

      if (response.data.length === 0) {
        return DeliveryStatus.UNKNOWN;
      }

      const event = response.data[0];
      const eventType = event.event;

      // Map SendGrid event types to our DeliveryStatus enum
      switch (eventType) {
        case 'processed':
          return DeliveryStatus.PROCESSED;
        case 'delivered':
          return DeliveryStatus.DELIVERED;
        case 'deferred':
          return DeliveryStatus.DEFERRED;
        case 'bounce':
          return DeliveryStatus.BOUNCED;
        case 'blocked':
          return DeliveryStatus.REJECTED;
        case 'dropped':
          return DeliveryStatus.DROPPED;
        case 'spamreport':
          return DeliveryStatus.COMPLAINED;
        case 'open':
          return DeliveryStatus.OPENED;
        case 'click':
          return DeliveryStatus.CLICKED;
        case 'unsubscribe':
          return DeliveryStatus.UNSUBSCRIBED;
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

      // Get the active version details
      const activeVersion = response.data.versions.find((v: any) => v.active === 1);

      if (!activeVersion) {
        throw new Error('No active version found for template');
      }

      // Get the specific version content
      const versionResponse = await this.apiClient.get(
        `/templates/${templateId}/versions/${activeVersion.id}`
      );

      return {
        id: templateId,
        name: response.data.name,
        subject: versionResponse.data.subject || '',
        html: versionResponse.data.html_content,
        text: versionResponse.data.plain_content,
        version: activeVersion.id,
        variables: this.extractVariablesFromTemplate(versionResponse.data.html_content),
        description: response.data.description || '',
        createdAt: new Date(response.data.created_at * 1000),
        updatedAt: new Date(activeVersion.updated_at * 1000)
      };
    } catch (error: any) {
      throw new Error(`Failed to get template: ${error.message}`);
    }
  }

  /**
   * Creates a template on SendGrid
   * @param template The template to create
   * @returns The created template
   */
  async createTemplate(template: Omit<EmailTemplate, 'id'>): Promise<EmailTemplate> {
    try {
      // First create the template
      const templateResponse = await this.apiClient.post('/templates', {
        name: template.name,
        generation: 'dynamic'
      });

      const templateId = templateResponse.data.id;

      // Then create a version for the template
      const versionResponse = await this.apiClient.post(`/templates/${templateId}/versions`, {
        name: `Version 1`,
        subject: template.subject,
        html_content: template.html,
        plain_content: template.text,
        active: 1
      });

      return {
        id: templateId,
        name: template.name,
        subject: template.subject,
        html: template.html,
        text: template.text,
        version: versionResponse.data.id,
        variables: this.extractVariablesFromTemplate(template.html || ''),
        description: template.description || '',
        createdAt: new Date(),
        updatedAt: new Date()
      };
    } catch (error: any) {
      throw new Error(`Failed to create template: ${error.message}`);
    }
  }

  /**
   * Updates a template on SendGrid
   * @param templateId The template ID
   * @param template The template data to update
   * @returns The updated template
   */
  async updateTemplate(templateId: string, template: Partial<EmailTemplate>): Promise<EmailTemplate> {
    try {
      // Update template name if provided
      if (template.name) {
        await this.apiClient.patch(`/templates/${templateId}`, {
          name: template.name
        });
      }

      // Get the current active version
      const templateResponse = await this.apiClient.get(`/templates/${templateId}`);
      const activeVersion = templateResponse.data.versions.find((v: any) => v.active === 1);

      if (!activeVersion) {
        throw new Error('No active version found for template');
      }

      // Create a new version with updated content
      const updatePayload: any = {
        name: `Updated Version`,
        active: 1
      };

      if (template.subject) updatePayload.subject = template.subject;
      if (template.html) updatePayload.html_content = template.html;
      if (template.text) updatePayload.plain_content = template.text;

      const versionResponse = await this.apiClient.post(
        `/templates/${templateId}/versions`,
        updatePayload
      );

      // Get the full updated template
      return await this.getTemplate(templateId);
    } catch (error: any) {
      throw new Error(`Failed to update template: ${error.message}`);
    }
  }

  /**
   * Deletes a template from SendGrid
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
   * Formats an email for SendGrid's API
   * @param email The email to format
   * @returns Formatted email payload for SendGrid
   */
  private formatEmailPayload(email: Email): any {
    const payload: any = {
      personalizations: [],
      from: { email: email.from },
      subject: email.subject,
      content: []
    };

    // Add HTML content if available
    if (email.html) {
      payload.content.push({
        type: 'text/html',
        value: email.html
      });
    }

    // Add text content if available
    if (email.text) {
      payload.content.push({
        type: 'text/plain',
        value: email.text
      });
    }

    // Create a personalization object for recipients
    const personalization: any = {};

    // Handle single recipient or multiple recipients
    personalization.to = Array.isArray(email.to)
      ? email.to.map(email => ({ email }))
      : [{ email: email.to }];

    // Add CC if provided
    if (email.cc) {
      personalization.cc = Array.isArray(email.cc)
        ? email.cc.map(email => ({ email }))
        : [{ email: email.cc }];
    }

    // Add BCC if provided
    if (email.bcc) {
      personalization.bcc = Array.isArray(email.bcc)
        ? email.bcc.map(email => ({ email }))
        : [{ email: email.bcc }];
    }

    // Add template data if using a template
    if (email.templateId) {
      payload.template_id = email.templateId;

      if (email.templateVars) {
        personalization.dynamic_template_data = email.templateVars;
      }
    }

    // Add the personalization to the payload
    payload.personalizations.push(personalization);

    // Add reply-to if provided
    if (email.replyTo) {
      payload.reply_to = { email: email.replyTo };
    }

    // Add headers if provided
    if (email.headers) {
      payload.headers = email.headers;
    }

    // Add attachments if provided
    if (email.attachments && email.attachments.length > 0) {
      payload.attachments = email.attachments.map(attachment => this.formatAttachment(attachment));
    }

    // Add categories if tags are provided
    if (email.tags && email.tags.length > 0) {
      payload.categories = email.tags;
    }

    // Add tracking settings based on tracking options
    if (email.tracking) {
      payload.tracking_settings = {
        click_tracking: {
          enable: !!email.tracking.clicks
        },
        open_tracking: {
          enable: !!email.tracking.opens
        },
        subscription_tracking: {
          enable: !!email.tracking.unsubscribe
        }
      };
    }

    return payload;
  }

  /**
   * Formats an attachment for SendGrid's API
   * @param attachment The attachment to format
   * @returns Formatted attachment for SendGrid
   */
  private formatAttachment(attachment: Attachment): any {
    let content: string;

    // Convert Buffer to base64 if needed
    if (Buffer.isBuffer(attachment.content)) {
      content = attachment.content.toString('base64');
    } else if (typeof attachment.content === 'string') {
      // Check if already base64
      if (this.isBase64(attachment.content)) {
        content = attachment.content;
      } else {
        content = Buffer.from(attachment.content).toString('base64');
      }
    } else {
      throw new Error('Unsupported attachment content type');
    }

    return {
      content,
      filename: attachment.filename,
      type: attachment.contentType,
      disposition: attachment.disposition || 'attachment',
      content_id: attachment.contentId
    };
  }

  /**
   * Checks if a string is base64 encoded
   * @param str The string to check
   * @returns True if the string is base64 encoded
   */
  private isBase64(str: string): boolean {
    try {
      return Buffer.from(str, 'base64').toString('base64') === str;
    } catch (error) {
      return false;
    }
  }

  /**
   * Generates a message ID for tracking
   * @param email The email for which to generate ID
   * @returns Generated message ID
   */
  private generateMessageId(email: Email): string {
    const timestamp = Date.now();
    const to = Array.isArray(email.to) ? email.to[0] : email.to;
    const hash = Buffer.from(`${to}:${email.subject}:${timestamp}`).toString('base64');
    return `sendgrid_${hash}`;
  }

  /**
   * Extracts variable names from a template
   * @param template The template HTML
   * @returns Array of variable names
   */
  private extractVariablesFromTemplate(template: string): string[] {
    if (!template) return [];

    const variables = new Set<string>();
    const handlebarsRegex = /{{([^{}]+)}}/g;
    const matches = template.match(handlebarsRegex);

    if (matches) {
      matches.forEach(match => {
        // Extract variable name between {{ and }}
        const variable = match.substring(2, match.length - 2).trim();
        variables.add(variable);
      });
    }

    return Array.from(variables);
  }
}
