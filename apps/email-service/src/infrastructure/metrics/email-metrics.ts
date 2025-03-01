/**
 * Email service metrics implementation
 */
import { EmailMetricsService } from '../../application/usecases/email-service';
import { Counter, Histogram, Registry } from 'prom-client';

/**
 * Prometheus-based implementation of email metrics
 */
export class PrometheusEmailMetrics implements EmailMetricsService {
  private readonly sendCounter: Counter<string>;
  private readonly sendDuration: Histogram<string>;
  private readonly deliveryCounter: Counter<string>;
  private readonly providerErrorCounter: Counter<string>;

  /**
   * Creates a new PrometheusEmailMetrics instance
   * @param registry Prometheus registry
   */
  constructor(private readonly registry: Registry) {
    this.sendCounter = new Counter({
      name: 'email_send_total',
      help: 'Total number of emails sent',
      labelNames: ['provider', 'template', 'status'],
      registers: [registry]
    });

    this.sendDuration = new Histogram({
      name: 'email_send_duration_seconds',
      help: 'Email sending duration in seconds',
      labelNames: ['provider'],
      buckets: [0.1, 0.5, 1, 2, 5, 10],
      registers: [registry]
    });

    this.deliveryCounter = new Counter({
      name: 'email_delivery_total',
      help: 'Total number of email deliveries',
      labelNames: ['provider', 'status'],
      registers: [registry]
    });

    this.providerErrorCounter = new Counter({
      name: 'email_provider_error_total',
      help: 'Total number of provider errors',
      labelNames: ['provider', 'error_type'],
      registers: [registry]
    });
  }

  /**
   * Records an email send attempt
   * @param provider Email provider name
   * @param template Template name or ID
   * @param status Status of the send operation
   */
  recordSend(provider: string, template: string, status: string): void {
    this.sendCounter.inc({ provider, template, status });
  }

  /**
   * Records the duration of an email send operation
   * @param provider Email provider name
   * @param durationMs Duration in milliseconds
   */
  recordSendDuration(provider: string, durationMs: number): void {
    this.sendDuration.observe({ provider }, durationMs / 1000);
  }

  /**
   * Records an email delivery status update
   * @param provider Email provider name
   * @param status Delivery status
   */
  recordDelivery(provider: string, status: string): void {
    this.deliveryCounter.inc({ provider, status });
  }

  /**
   * Records a provider error
   * @param provider Email provider name
   * @param errorType Type of error
   */
  recordProviderError(provider: string, errorType: string): void {
    this.providerErrorCounter.inc({ provider, error_type: errorType });
  }
}
