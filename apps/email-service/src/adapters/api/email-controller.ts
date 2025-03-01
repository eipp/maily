/**
 * Email API Controller
 */
import { Router, Request, Response } from 'express';
import { EmailService } from '../../application/usecases/email-service';
import { Email, DeliveryStatus } from '../../domain/models';
import { validate } from 'class-validator';
import { plainToClass } from 'class-transformer';
import { EmailDto, BulkEmailDto } from './dtos/email.dto';

/**
 * Controller for email-related endpoints
 */
export class EmailController {
  private router: Router;

  /**
   * Creates a new EmailController instance
   * @param emailService Email service
   */
  constructor(private readonly emailService: EmailService) {
    this.router = Router();
    this.initializeRoutes();
  }

  /**
   * Gets the controller router
   * @returns Express router with configured routes
   */
  getRouter(): Router {
    return this.router;
  }

  /**
   * Initializes controller routes
   */
  private initializeRoutes(): void {
    // Send single email
    this.router.post('/send', this.sendEmail.bind(this));

    // Send bulk emails
    this.router.post('/send-bulk', this.sendBulkEmails.bind(this));

    // Check delivery status
    this.router.get('/status/:messageId', this.getStatus.bind(this));

    // Template operations
    this.router.get('/templates/:templateId', this.getTemplate.bind(this));
    this.router.post('/templates', this.createTemplate.bind(this));
    this.router.put('/templates/:templateId', this.updateTemplate.bind(this));
    this.router.delete('/templates/:templateId', this.deleteTemplate.bind(this));

    // Render template (preview)
    this.router.post('/templates/:templateId/render', this.renderTemplate.bind(this));

    // Health check
    this.router.get('/health', (req: Request, res: Response) => {
      res.status(200).json({ status: 'ok' });
    });
  }

  /**
   * Sends a single email
   * @param req Express request
   * @param res Express response
   */
  private async sendEmail(req: Request, res: Response): Promise<void> {
    try {
      // Validate request body
      const emailDto = plainToClass(EmailDto, req.body);
      const errors = await validate(emailDto);

      if (errors.length > 0) {
        res.status(400).json({
          success: false,
          errors: errors.map(error => ({
            property: error.property,
            constraints: error.constraints
          }))
        });
        return;
      }

      // Convert DTO to domain model
      const email: Email = {
        from: emailDto.from,
        to: emailDto.to,
        subject: emailDto.subject,
        html: emailDto.html,
        text: emailDto.text,
        cc: emailDto.cc,
        bcc: emailDto.bcc,
        replyTo: emailDto.replyTo,
        headers: emailDto.headers,
        attachments: emailDto.attachments,
        templateId: emailDto.templateId,
        templateVars: emailDto.templateVars,
        tracking: emailDto.tracking,
        metadata: emailDto.metadata,
        tags: emailDto.tags,
        priority: emailDto.priority
      };

      // Send the email
      const result = await this.emailService.sendEmail(email);

      // Return response
      if (result.success) {
        res.status(200).json({
          success: true,
          messageId: result.messageId,
          sentAt: result.sentAt
        });
      } else {
        res.status(500).json({
          success: false,
          error: result.error
        });
      }
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to send email'
      });
    }
  }

  /**
   * Sends multiple emails in bulk
   * @param req Express request
   * @param res Express response
   */
  private async sendBulkEmails(req: Request, res: Response): Promise<void> {
    try {
      // Validate request body
      const bulkEmailDto = plainToClass(BulkEmailDto, req.body);
      const errors = await validate(bulkEmailDto);

      if (errors.length > 0) {
        res.status(400).json({
          success: false,
          errors: errors.map(error => ({
            property: error.property,
            constraints: error.constraints
          }))
        });
        return;
      }

      // Convert DTOs to domain models
      const emails: Email[] = bulkEmailDto.emails.map(emailDto => ({
        from: emailDto.from,
        to: emailDto.to,
        subject: emailDto.subject,
        html: emailDto.html,
        text: emailDto.text,
        cc: emailDto.cc,
        bcc: emailDto.bcc,
        replyTo: emailDto.replyTo,
        headers: emailDto.headers,
        attachments: emailDto.attachments,
        templateId: emailDto.templateId,
        templateVars: emailDto.templateVars,
        tracking: emailDto.tracking,
        metadata: emailDto.metadata,
        tags: emailDto.tags,
        priority: emailDto.priority
      }));

      // Send the emails in bulk
      const result = await this.emailService.sendBulk(emails);

      // Return response
      res.status(result.success ? 200 : 500).json({
        success: result.success,
        total: result.total,
        sent: result.sent,
        failed: result.failed,
        results: result.results.map(r => ({
          to: r.to,
          success: r.success,
          messageId: r.messageId,
          error: r.error,
          sentAt: r.sentAt
        }))
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to send bulk emails'
      });
    }
  }

  /**
   * Gets the delivery status of an email
   * @param req Express request
   * @param res Express response
   */
  private async getStatus(req: Request, res: Response): Promise<void> {
    try {
      const messageId = req.params.messageId;

      if (!messageId) {
        res.status(400).json({
          success: false,
          error: 'Message ID is required'
        });
        return;
      }

      // Get the delivery status
      const status = await this.emailService.getDeliveryStatus(messageId);

      // Return response
      res.status(200).json({
        success: true,
        messageId,
        status,
        timestamp: new Date()
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get delivery status'
      });
    }
  }

  /**
   * Gets a template by ID
   * @param req Express request
   * @param res Express response
   */
  private async getTemplate(req: Request, res: Response): Promise<void> {
    try {
      const templateId = req.params.templateId;

      if (!templateId) {
        res.status(400).json({
          success: false,
          error: 'Template ID is required'
        });
        return;
      }

      // Get the template
      const template = await this.emailService.getTemplate(templateId);

      // Return response
      res.status(200).json({
        success: true,
        template
      });
    } catch (error: any) {
      res.status(404).json({
        success: false,
        error: error.message || 'Failed to get template'
      });
    }
  }

  /**
   * Creates a new template
   * @param req Express request
   * @param res Express response
   */
  private async createTemplate(req: Request, res: Response): Promise<void> {
    try {
      const { name, subject, html, text, description } = req.body;

      if (!name || (!html && !text)) {
        res.status(400).json({
          success: false,
          error: 'Name and either HTML or text content are required'
        });
        return;
      }

      // Create the template
      const template = await this.emailService.createTemplate({
        name,
        subject: subject || '',
        html,
        text,
        description
      });

      // Return response
      res.status(201).json({
        success: true,
        template
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to create template'
      });
    }
  }

  /**
   * Updates an existing template
   * @param req Express request
   * @param res Express response
   */
  private async updateTemplate(req: Request, res: Response): Promise<void> {
    try {
      const templateId = req.params.templateId;
      const { name, subject, html, text, description } = req.body;

      if (!templateId) {
        res.status(400).json({
          success: false,
          error: 'Template ID is required'
        });
        return;
      }

      if (Object.keys(req.body).length === 0) {
        res.status(400).json({
          success: false,
          error: 'No update fields provided'
        });
        return;
      }

      // Update the template
      const template = await this.emailService.updateTemplate(templateId, {
        name,
        subject,
        html,
        text,
        description
      });

      // Return response
      res.status(200).json({
        success: true,
        template
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to update template'
      });
    }
  }

  /**
   * Deletes a template
   * @param req Express request
   * @param res Express response
   */
  private async deleteTemplate(req: Request, res: Response): Promise<void> {
    try {
      const templateId = req.params.templateId;

      if (!templateId) {
        res.status(400).json({
          success: false,
          error: 'Template ID is required'
        });
        return;
      }

      // Delete the template
      const success = await this.emailService.deleteTemplate(templateId);

      // Return response
      if (success) {
        res.status(200).json({
          success: true,
          message: `Template ${templateId} deleted successfully`
        });
      } else {
        res.status(404).json({
          success: false,
          error: `Template ${templateId} not found or could not be deleted`
        });
      }
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to delete template'
      });
    }
  }

  /**
   * Renders a template with variables
   * @param req Express request
   * @param res Express response
   */
  private async renderTemplate(req: Request, res: Response): Promise<void> {
    try {
      const templateId = req.params.templateId;
      const variables = req.body.variables || {};

      if (!templateId) {
        res.status(400).json({
          success: false,
          error: 'Template ID is required'
        });
        return;
      }

      // Render the template
      const rendered = await this.emailService.renderTemplate(templateId, variables);

      // Return response
      res.status(200).json({
        success: true,
        rendered
      });
    } catch (error: any) {
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to render template'
      });
    }
  }
}
