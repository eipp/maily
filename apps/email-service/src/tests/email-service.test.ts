/**
 * Email Service Test Suite
 */
import { EmailService } from '../application/usecases/email-service';
import { Email, DeliveryStatus, SendResult, BulkSendResult } from '../domain/models';
import { EmailProvider, EmailRepository } from '../domain/interfaces';

// Create mock implementations
class MockEmailProvider implements EmailProvider {
  readonly providerName = 'mock';
  private messageIdCounter = 1;
  private mockDeliveryStatus: DeliveryStatus = DeliveryStatus.DELIVERED;
  private shouldFail = false;
  private templates: Record<string, any> = {};

  setShouldFail(value: boolean): void {
    this.shouldFail = value;
  }

  setMockDeliveryStatus(status: DeliveryStatus): void {
    this.mockDeliveryStatus = status;
  }

  async sendEmail(email: Email): Promise<SendResult> {
    if (this.shouldFail) {
      return {
        success: false,
        error: 'Mock provider error',
        sentAt: new Date()
      };
    }

    return {
      success: true,
      messageId: `mock-${this.messageIdCounter++}`,
      providerResponse: { email },
      sentAt: new Date()
    };
  }

  async sendBulk(emails: Email[]): Promise<BulkSendResult> {
    if (this.shouldFail) {
      return {
        success: false,
        total: emails.length,
        sent: 0,
        failed: emails.length,
        results: emails.map(email => ({
          success: false,
          to: Array.isArray(email.to) ? email.to[0] : email.to,
          error: 'Mock provider error',
          sentAt: new Date()
        }))
      };
    }

    return {
      success: true,
      total: emails.length,
      sent: emails.length,
      failed: 0,
      results: emails.map(email => ({
        success: true,
        messageId: `mock-${this.messageIdCounter++}`,
        to: Array.isArray(email.to) ? email.to[0] : email.to,
        sentAt: new Date()
      }))
    };
  }

  async getDeliveryStatus(messageId: string): Promise<DeliveryStatus> {
    return this.mockDeliveryStatus;
  }

  async getTemplate(templateId: string): Promise<any> {
    if (!this.templates[templateId]) {
      throw new Error(`Template ${templateId} not found`);
    }
    return this.templates[templateId];
  }

  async createTemplate(template: any): Promise<any> {
    const id = `template-${Object.keys(this.templates).length + 1}`;
    this.templates[id] = { ...template, id };
    return this.templates[id];
  }

  async updateTemplate(templateId: string, template: any): Promise<any> {
    if (!this.templates[templateId]) {
      throw new Error(`Template ${templateId} not found`);
    }
    this.templates[templateId] = { ...this.templates[templateId], ...template };
    return this.templates[templateId];
  }

  async deleteTemplate(templateId: string): Promise<boolean> {
    if (!this.templates[templateId]) {
      return false;
    }
    delete this.templates[templateId];
    return true;
  }
}

class MockEmailRepository implements EmailRepository {
  private emails: Record<string, Email> = {};
  private idCounter = 1;
  // Track statuses separately
  private statuses: Record<string, DeliveryStatus> = {};

  async saveEmail(email: Email): Promise<Email> {
    const id = email.id || `email-${this.idCounter++}`;
    const savedEmail = { ...email, id };
    this.emails[id] = savedEmail;
    return savedEmail;
  }

  async getEmailById(emailId: string): Promise<Email | null> {
    return this.emails[emailId] || null;
  }

  async updateDeliveryStatus(emailId: string, status: DeliveryStatus): Promise<boolean> {
    if (!this.emails[emailId]) {
      return false;
    }
    this.statuses[emailId] = status;
    return true;
  }

  async queryEmails(filter: Record<string, any>, page: number, pageSize: number): Promise<{ emails: Email[]; total: number }> {
    const emails = Object.values(this.emails);
    return {
      emails: emails.slice((page - 1) * pageSize, page * pageSize),
      total: emails.length
    };
  }
}

class MockEmailMetricsService {
  recordSend = jest.fn();
  recordSendDuration = jest.fn();
  recordDelivery = jest.fn();
  recordProviderError = jest.fn();
}

class MockEmailRateLimiter {
  private shouldAllow = true;

  setShouldAllow(value: boolean): void {
    this.shouldAllow = value;
  }

  async allowSend(): Promise<boolean> {
    return this.shouldAllow;
  }
}

describe('EmailService', () => {
  let emailService: EmailService;
  let mockEmailProvider: MockEmailProvider;
  let mockEmailRepository: MockEmailRepository;
  let mockMetricsService: MockEmailMetricsService;
  let mockRateLimiter: MockEmailRateLimiter;

  beforeEach(() => {
    mockEmailProvider = new MockEmailProvider();
    mockEmailRepository = new MockEmailRepository();
    mockMetricsService = new MockEmailMetricsService();
    mockRateLimiter = new MockEmailRateLimiter();

    emailService = new EmailService(
      mockEmailProvider,
      mockEmailRepository,
      mockMetricsService,
      mockRateLimiter
    );
  });

  describe('sendEmail', () => {
    const testEmail: Email = {
      from: 'test@example.com',
      to: 'recipient@example.com',
      subject: 'Test Email',
      html: '<p>Hello World</p>',
      text: 'Hello World'
    };

    it('should send email with correct parameters', async () => {
      const result = await emailService.sendEmail(testEmail);

      expect(result.success).toBe(true);
      expect(result.messageId).toBeDefined();
      expect(mockMetricsService.recordSend).toHaveBeenCalled();
      expect(mockMetricsService.recordSendDuration).toHaveBeenCalled();
    });

    it('should handle provider errors gracefully', async () => {
      mockEmailProvider.setShouldFail(true);

      const result = await emailService.sendEmail(testEmail);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(mockMetricsService.recordProviderError).toHaveBeenCalled();
    });

    it('should respect rate limits', async () => {
      mockRateLimiter.setShouldAllow(false);

      // Implementation would need to be updated to check rate limits
      // This test verifies behavior if that check was implemented
      // For now, it's a placeholder for future implementation
    });
  });

  describe('sendBulk', () => {
    const testEmails: Email[] = [
      {
        from: 'test@example.com',
        to: 'recipient1@example.com',
        subject: 'Test Email 1',
        html: '<p>Hello World 1</p>'
      },
      {
        from: 'test@example.com',
        to: 'recipient2@example.com',
        subject: 'Test Email 2',
        html: '<p>Hello World 2</p>'
      }
    ];

    it('should send bulk emails successfully', async () => {
      const result = await emailService.sendBulk(testEmails);

      expect(result.success).toBe(true);
      expect(result.total).toBe(2);
      expect(result.sent).toBe(2);
      expect(result.failed).toBe(0);
      expect(result.results.length).toBe(2);
      expect(mockMetricsService.recordSend).toHaveBeenCalled();
      expect(mockMetricsService.recordSendDuration).toHaveBeenCalled();
    });

    it('should handle bulk send failures', async () => {
      mockEmailProvider.setShouldFail(true);

      const result = await emailService.sendBulk(testEmails);

      expect(result.success).toBe(false);
      expect(result.total).toBe(2);
      expect(result.failed).toBe(2);
      expect(mockMetricsService.recordProviderError).toHaveBeenCalled();
    });
  });

  describe('getDeliveryStatus', () => {
    it('should return the correct delivery status', async () => {
      mockEmailProvider.setMockDeliveryStatus(DeliveryStatus.DELIVERED);

      const status = await emailService.getDeliveryStatus('mock-123');

      expect(status).toBe(DeliveryStatus.DELIVERED);
      expect(mockMetricsService.recordDelivery).toHaveBeenCalledWith(
        'mock',
        DeliveryStatus.DELIVERED
      );
    });

    it('should handle errors when getting delivery status', async () => {
      mockEmailProvider.setShouldFail(true);

      // Implementation would need to handle this case
      // This test verifies behavior if that error handling was implemented
      // For now, it's a placeholder for future implementation
    });
  });

  describe('template operations', () => {
    const testTemplate = {
      name: 'Test Template',
      subject: 'Test Subject',
      html: '<p>Hello {{name}}</p>',
      text: 'Hello {{name}}'
    };

    it('should create a template', async () => {
      const result = await emailService.createTemplate(testTemplate);

      expect(result.id).toBeDefined();
      expect(result.name).toBe(testTemplate.name);
      expect(result.subject).toBe(testTemplate.subject);
    });

    it('should get a template', async () => {
      const created = await emailService.createTemplate(testTemplate);
      const retrieved = await emailService.getTemplate(created.id);

      expect(retrieved.id).toBe(created.id);
      expect(retrieved.name).toBe(testTemplate.name);
    });

    it('should update a template', async () => {
      const created = await emailService.createTemplate(testTemplate);
      const updated = await emailService.updateTemplate(created.id, {
        subject: 'Updated Subject'
      });

      expect(updated.id).toBe(created.id);
      expect(updated.subject).toBe('Updated Subject');
      expect(updated.name).toBe(testTemplate.name);
    });

    it('should delete a template', async () => {
      const created = await emailService.createTemplate(testTemplate);
      const result = await emailService.deleteTemplate(created.id);

      expect(result).toBe(true);
    });

    it('should render a template with variables', async () => {
      const created = await emailService.createTemplate(testTemplate);

      // Implementation would need to be tested
      // This test verifies behavior if that template rendering was implemented
      // For now, it's a placeholder for future implementation
    });
  });
});
