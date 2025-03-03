import { jest } from '@jest/globals';

/**
 * Interface for the email service that sends emails
 */
export interface EmailService {
  sendEmail(options: {
    to: string | string[];
    subject: string;
    html: string;
    text?: string;
    from?: string;
    replyTo?: string;
    attachments?: Array<{
      filename: string;
      content: Buffer | string;
      contentType?: string;
    }>;
    metadata?: Record<string, string>;
  }): Promise<{
    messageId: string;
    status: 'sent' | 'queued' | 'failed';
  }>;
  
  sendBulkEmails(options: Array<{
    to: string;
    subject: string;
    html: string;
    text?: string;
    from?: string;
    replyTo?: string;
    attachments?: Array<{
      filename: string;
      content: Buffer | string;
      contentType?: string;
    }>;
    metadata?: Record<string, string>;
  }>): Promise<Array<{
    messageId: string;
    status: 'sent' | 'queued' | 'failed';
    to: string;
  }>>;
  
  getDeliveryStatus(messageId: string): Promise<{
    status: 'delivered' | 'failed' | 'bounced' | 'queued' | 'sending' | 'unknown';
    details?: string;
  }>;
}

/**
 * Creates a mock email service for testing
 * 
 * @returns A mocked implementation of the EmailService interface
 */
export function mockEmailService(): jest.Mocked<EmailService> {
  return {
    sendEmail: jest.fn().mockImplementation(async () => ({
      messageId: `message-${Date.now()}`,
      status: 'sent',
    })),
    
    sendBulkEmails: jest.fn().mockImplementation(async (options) => {
      return options.map(option => ({
        messageId: `message-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        status: 'sent',
        to: option.to,
      }));
    }),
    
    getDeliveryStatus: jest.fn().mockImplementation(async () => ({
      status: 'delivered',
    })),
  };
}