/**
 * Email repository implementation
 */
import { Repository } from 'typeorm';
import { EmailRepository } from '../../domain/interfaces';
import { Email, DeliveryStatus } from '../../domain/models';
import { EmailEntity } from '../entities/email.entity';

/**
 * TypeORM implementation of the email repository
 */
export class TypeOrmEmailRepository implements EmailRepository {
  /**
   * Creates a new TypeOrmEmailRepository instance
   * @param repository TypeORM repository for EmailEntity
   */
  constructor(private readonly repository: Repository<EmailEntity>) {}

  /**
   * Saves an email record
   * @param email The email to save
   * @returns The saved email with ID
   */
  async saveEmail(email: Email): Promise<Email> {
    // Convert domain model to entity
    const entity = this.toEntity(email);

    // Save entity to database
    const savedEntity = await this.repository.save(entity);

    // Convert back to domain model and return
    return this.toDomain(savedEntity);
  }

  /**
   * Gets an email by ID
   * @param emailId The email ID
   * @returns The email if found
   */
  async getEmailById(emailId: string): Promise<Email | null> {
    const entity = await this.repository.findOne({ where: { id: emailId } });

    if (!entity) {
      return null;
    }

    return this.toDomain(entity);
  }

  /**
   * Updates email delivery status
   * @param emailId The email ID
   * @param status The new delivery status
   * @returns True if update was successful
   */
  async updateDeliveryStatus(emailId: string, status: DeliveryStatus): Promise<boolean> {
    const result = await this.repository.update(
      { id: emailId },
      {
        deliveryStatus: status,
        updatedAt: new Date()
      }
    );

    return result.affected !== undefined && result.affected > 0;
  }

  /**
   * Queries emails by filter criteria
   * @param filter The filter criteria
   * @param page Pagination page number
   * @param pageSize Page size for pagination
   * @returns Paginated list of emails
   */
  async queryEmails(
    filter: Record<string, any>,
    page: number,
    pageSize: number
  ): Promise<{ emails: Email[]; total: number }> {
    // Build query based on filter criteria
    const queryBuilder = this.repository.createQueryBuilder('email');

    // Apply filters
    if (filter.from) {
      queryBuilder.andWhere('email.from = :from', { from: filter.from });
    }

    if (filter.to) {
      queryBuilder.andWhere('email.to LIKE :to', { to: `%${filter.to}%` });
    }

    if (filter.subject) {
      queryBuilder.andWhere('email.subject LIKE :subject', { subject: `%${filter.subject}%` });
    }

    if (filter.status) {
      queryBuilder.andWhere('email.deliveryStatus = :status', { status: filter.status });
    }

    if (filter.sentAfter) {
      queryBuilder.andWhere('email.sentAt >= :sentAfter', { sentAfter: filter.sentAfter });
    }

    if (filter.sentBefore) {
      queryBuilder.andWhere('email.sentAt <= :sentBefore', { sentBefore: filter.sentBefore });
    }

    // Add pagination
    queryBuilder
      .skip((page - 1) * pageSize)
      .take(pageSize)
      .orderBy('email.createdAt', 'DESC');

    // Execute query
    const [entities, total] = await queryBuilder.getManyAndCount();

    // Convert entities to domain models
    const emails = entities.map(entity => this.toDomain(entity));

    return { emails, total };
  }

  /**
   * Converts domain model to entity
   * @param email Domain email model
   * @returns Email entity
   */
  private toEntity(email: Email): EmailEntity {
    const entity = new EmailEntity();

    // Map properties
    entity.id = email.id;
    entity.from = email.from;
    entity.to = Array.isArray(email.to) ? email.to.join(', ') : email.to || '';
    entity.subject = email.subject;
    entity.html = email.html || null;
    entity.text = email.text || null;
    entity.cc = Array.isArray(email.cc) ? email.cc.join(', ') : (email.cc || null);
    entity.bcc = Array.isArray(email.bcc) ? email.bcc.join(', ') : (email.bcc || null);
    entity.replyTo = email.replyTo || null;
    entity.headers = email.headers ? JSON.stringify(email.headers) : null;
    entity.templateId = email.templateId || null;
    entity.templateVars = email.templateVars ? JSON.stringify(email.templateVars) : null;
    entity.tracking = email.tracking ? JSON.stringify(email.tracking) : null;
    entity.metadata = email.metadata ? JSON.stringify(email.metadata) : null;
    entity.tags = email.tags ? email.tags.join(', ') : null;
    entity.priority = email.priority || 'normal';

    return entity;
  }

  /**
   * Converts entity to domain model
   * @param entity Email entity
   * @returns Domain email model
   */
  private toDomain(entity: EmailEntity): Email {
    return {
      id: entity.id,
      from: entity.from,
      to: entity.to.includes(',') ? entity.to.split(',').map(s => s.trim()) : entity.to,
      subject: entity.subject,
      html: entity.html || undefined,
      text: entity.text || undefined,
      cc: entity.cc ? (entity.cc.includes(',') ? entity.cc.split(',').map(s => s.trim()) : entity.cc) : undefined,
      bcc: entity.bcc ? (entity.bcc.includes(',') ? entity.bcc.split(',').map(s => s.trim()) : entity.bcc) : undefined,
      replyTo: entity.replyTo || undefined,
      headers: entity.headers ? JSON.parse(entity.headers) : undefined,
      templateId: entity.templateId || undefined,
      templateVars: entity.templateVars ? JSON.parse(entity.templateVars) : undefined,
      tracking: entity.tracking ? JSON.parse(entity.tracking) : undefined,
      metadata: entity.metadata ? JSON.parse(entity.metadata) : undefined,
      tags: entity.tags ? entity.tags.split(',').map(s => s.trim()) : undefined,
      priority: entity.priority as 'high' | 'normal' | 'low'
    };
  }
}
