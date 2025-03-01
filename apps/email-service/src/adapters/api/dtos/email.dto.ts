/**
 * Email DTOs for API layer validation
 */
import {
  IsString,
  IsArray,
  IsOptional,
  IsEnum,
  IsObject,
  IsEmail,
  ValidateNested,
  ArrayMinSize
} from 'class-validator';
import { Type } from 'class-transformer';

/**
 * Priority levels for emails
 */
enum Priority {
  HIGH = 'high',
  NORMAL = 'normal',
  LOW = 'low'
}

/**
 * Attachment DTO
 */
export class AttachmentDto {
  @IsString()
  filename: string;

  @IsString()
  content: string;

  @IsString()
  @IsOptional()
  contentType?: string;

  @IsString()
  @IsOptional()
  contentId?: string;

  @IsEnum(['inline', 'attachment'])
  @IsOptional()
  disposition?: 'inline' | 'attachment';
}

/**
 * Tracking options DTO
 */
export class TrackingDto {
  @IsOptional()
  opens?: boolean;

  @IsOptional()
  clicks?: boolean;

  @IsOptional()
  unsubscribe?: boolean;
}

/**
 * Single email DTO
 */
export class EmailDto {
  @IsEmail()
  from: string;

  @IsEmail({}, { each: true })
  to: string | string[];

  @IsString()
  subject: string;

  @IsString()
  @IsOptional()
  html?: string;

  @IsString()
  @IsOptional()
  text?: string;

  @IsEmail({}, { each: true })
  @IsOptional()
  cc?: string | string[];

  @IsEmail({}, { each: true })
  @IsOptional()
  bcc?: string | string[];

  @IsEmail()
  @IsOptional()
  replyTo?: string;

  @IsObject()
  @IsOptional()
  headers?: Record<string, string>;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => AttachmentDto)
  @IsOptional()
  attachments?: AttachmentDto[];

  @IsString()
  @IsOptional()
  templateId?: string;

  @IsObject()
  @IsOptional()
  templateVars?: Record<string, any>;

  @ValidateNested()
  @Type(() => TrackingDto)
  @IsOptional()
  tracking?: TrackingDto;

  @IsObject()
  @IsOptional()
  metadata?: Record<string, any>;

  @IsArray()
  @IsString({ each: true })
  @IsOptional()
  tags?: string[];

  @IsEnum(Priority)
  @IsOptional()
  priority?: 'high' | 'normal' | 'low';
}

/**
 * Bulk email DTO
 */
export class BulkEmailDto {
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => EmailDto)
  @ArrayMinSize(1)
  emails: EmailDto[];
}
