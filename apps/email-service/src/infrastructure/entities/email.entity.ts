/**
 * Email entity for database storage
 */
import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  CreateDateColumn,
  UpdateDateColumn,
  Index
} from 'typeorm';

/**
 * Email entity for database persistence
 */
@Entity('emails')
export class EmailEntity {
  /**
   * Unique identifier
   */
  @PrimaryGeneratedColumn('uuid')
  id: string;

  /**
   * Sender email address
   */
  @Column()
  @Index()
  from: string;

  /**
   * Recipient email addresses (comma-separated)
   */
  @Column()
  @Index()
  to: string;

  /**
   * Email subject
   */
  @Column()
  @Index()
  subject: string;

  /**
   * HTML content
   */
  @Column({ type: 'text', nullable: true })
  html: string | null;

  /**
   * Plain text content
   */
  @Column({ type: 'text', nullable: true })
  text: string | null;

  /**
   * Carbon copy recipients (comma-separated)
   */
  @Column({ nullable: true })
  cc: string | null;

  /**
   * Blind carbon copy recipients (comma-separated)
   */
  @Column({ nullable: true })
  bcc: string | null;

  /**
   * Reply-to address
   */
  @Column({ nullable: true })
  replyTo: string | null;

  /**
   * Email headers (JSON string)
   */
  @Column({ type: 'text', nullable: true })
  headers: string | null;

  /**
   * Template ID if using a template
   */
  @Column({ nullable: true })
  @Index()
  templateId: string | null;

  /**
   * Template variables (JSON string)
   */
  @Column({ type: 'text', nullable: true })
  templateVars: string | null;

  /**
   * Tracking options (JSON string)
   */
  @Column({ type: 'text', nullable: true })
  tracking: string | null;

  /**
   * Metadata for tracking and analytics (JSON string)
   */
  @Column({ type: 'text', nullable: true })
  metadata: string | null;

  /**
   * Tags for categorization (comma-separated)
   */
  @Column({ nullable: true })
  tags: string | null;

  /**
   * Priority level
   */
  @Column({ default: 'normal' })
  priority: string;

  /**
   * Provider used to send this email
   */
  @Column({ nullable: true })
  @Index()
  provider: string | null;

  /**
   * Message ID from the provider
   */
  @Column({ nullable: true })
  @Index()
  providerMessageId: string | null;

  /**
   * Current delivery status
   */
  @Column({ default: 'pending' })
  @Index()
  deliveryStatus: string;

  /**
   * Error message if send failed
   */
  @Column({ type: 'text', nullable: true })
  error: string | null;

  /**
   * Last error timestamp
   */
  @Column({ type: 'timestamp', nullable: true })
  lastErrorAt: Date | null;

  /**
   * Number of send attempts
   */
  @Column({ default: 0 })
  attempts: number;

  /**
   * Timestamp when the email was sent
   */
  @Column({ type: 'timestamp', nullable: true })
  sentAt: Date | null;

  /**
   * Timestamp when the email was delivered
   */
  @Column({ type: 'timestamp', nullable: true })
  deliveredAt: Date | null;

  /**
   * Timestamp when the email was opened
   */
  @Column({ type: 'timestamp', nullable: true })
  openedAt: Date | null;

  /**
   * Timestamp when the email was clicked
   */
  @Column({ type: 'timestamp', nullable: true })
  clickedAt: Date | null;

  /**
   * User or system that created this email
   */
  @Column({ nullable: true })
  createdBy: string | null;

  /**
   * Creation timestamp
   */
  @CreateDateColumn()
  createdAt: Date;

  /**
   * Last update timestamp
   */
  @UpdateDateColumn()
  updatedAt: Date;
}
