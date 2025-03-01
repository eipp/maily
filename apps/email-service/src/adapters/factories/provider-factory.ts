/**
 * Email provider factory
 */
import { EmailProvider } from '../../domain/interfaces';
import { ResendEmailProvider } from '../providers/resend-provider';
import { SendGridEmailProvider } from '../providers/sendgrid-provider';
import { MailgunEmailProvider } from '../providers/mailgun-provider';

/**
 * Provider types supported by the factory
 */
export type ProviderType = 'resend' | 'sendgrid' | 'mailgun';

/**
 * Provider configuration options
 */
export interface ProviderConfig {
  type: ProviderType;
  apiKey: string;
  domain?: string; // Required for Mailgun
  region?: 'us' | 'eu'; // Optional for Mailgun
}

/**
 * Factory for creating email providers
 */
export class EmailProviderFactory {
  /**
   * Creates an email provider based on configuration
   * @param config Provider configuration
   * @returns Email provider instance
   */
  static createProvider(config: ProviderConfig): EmailProvider {
    switch (config.type) {
      case 'resend':
        return new ResendEmailProvider(config.apiKey);

      case 'sendgrid':
        return new SendGridEmailProvider(config.apiKey);

      case 'mailgun':
        if (!config.domain) {
          throw new Error('Domain is required for Mailgun provider');
        }
        return new MailgunEmailProvider(
          config.apiKey,
          config.domain,
          config.region
        );

      default:
        throw new Error(`Unsupported provider type: ${config.type}`);
    }
  }
}
