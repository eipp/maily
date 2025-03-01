import * as amplitude from '@amplitude/analytics-browser';
import { z } from 'zod';

export interface CampaignAnalytics {
  openRate: number;
  clickRate: number;
  conversionRate: number;
  engagement: number;
}

// Validation schema for analytics data
const analyticsDataSchema = z.object({
  openRate: z.number().min(0).max(100),
  clickRate: z.number().min(0).max(100),
  conversionRate: z.number().min(0).max(100),
  engagement: z.number().min(0).max(100),
});

class AnalyticsService {
  private initialized = false;
  private readonly maxRetries = 3;
  private readonly baseDelay = 1000; // 1 second

  /**
   * Initialize Amplitude analytics with enhanced configuration
   */
  init() {
    if (this.initialized) return;

    amplitude.init(process.env.NEXT_PUBLIC_AMPLITUDE_API_KEY!, {
      defaultTracking: true,
      logLevel:
        process.env.NODE_ENV === 'production'
          ? amplitude.Types.LogLevel.None
          : amplitude.Types.LogLevel.Debug,
      minIdLength: 1,
      uploadBatchSize: 100,
      flushQueueSize: 200,
      flushIntervalMillis: 10000,
      optOut: false,
      platform: 'Web',
    });

    // Track initialization
    this.trackEvent('analytics_initialized', {
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV,
    });

    this.initialized = true;
  }

  /**
   * Fetch campaign analytics data with retries and validation
   */
  async getCampaignAnalytics(
    campaignId: string,
    retryCount = 0
  ): Promise<CampaignAnalytics> {
    const startTime = performance.now();

    try {
      const response = await fetch(`/api/analytics/${campaignId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Validate response data
      const validatedData = analyticsDataSchema.parse(data);

      // Track successful fetch
      this.trackPerformance('analytics_fetch', performance.now() - startTime, {
        campaign_id: campaignId,
        success: true,
        retry_count: retryCount,
      });

      return validatedData;
    } catch (error) {
      // Track error
      this.trackError(error as Error, {
        context: 'get_campaign_analytics',
        campaign_id: campaignId,
        retry_count: retryCount,
      });

      // Implement exponential backoff for retries
      if (retryCount < this.maxRetries) {
        const delay = this.baseDelay * Math.pow(2, retryCount);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.getCampaignAnalytics(campaignId, retryCount + 1);
      }

      throw error;
    }
  }

  /**
   * Track a user event with enhanced metadata
   */
  trackEvent(eventName: string, properties: Record<string, any> = {}) {
    if (!this.initialized) this.init();

    const enhancedProperties = {
      ...properties,
      timestamp: new Date().toISOString(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      referrer: typeof document !== 'undefined' ? document.referrer : undefined,
    };

    amplitude.track(eventName, enhancedProperties);
  }

  /**
   * Set user properties with validation
   */
  setUserProperties(properties: Record<string, any>) {
    if (!this.initialized) this.init();

    const identify = new amplitude.Identify();

    Object.entries(properties).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        identify.set(key, value);
      }
    });

    amplitude.identify(identify);
  }

  /**
   * Set user ID with additional context
   */
  setUserId(userId: string) {
    if (!this.initialized) this.init();

    amplitude.setUserId(userId);

    this.trackEvent('user_identified', {
      user_id: userId,
    });
  }

  /**
   * Track page view with enhanced metadata
   */
  trackPageView(pageName: string, properties: Record<string, any> = {}) {
    const enhancedProperties = {
      page_name: pageName,
      path: typeof window !== 'undefined' ? window.location.pathname : undefined,
      query: typeof window !== 'undefined' ? window.location.search : undefined,
      ...properties,
    };

    this.trackEvent('page_view', enhancedProperties);
  }

  /**
   * Track campaign events with validation
   */
  trackCampaign(action: string, campaignId: string, properties: Record<string, any> = {}) {
    if (!campaignId) {
      console.warn('Campaign ID is required for tracking campaign events');
      return;
    }

    this.trackEvent(`campaign_${action}`, {
      campaign_id: campaignId,
      ...properties,
    });
  }

  /**
   * Track email events with validation
   */
  trackEmail(action: string, emailId: string, properties: Record<string, any> = {}) {
    if (!emailId) {
      console.warn('Email ID is required for tracking email events');
      return;
    }

    this.trackEvent(`email_${action}`, {
      email_id: emailId,
      ...properties,
    });
  }

  /**
   * Track subscription events with validation
   */
  trackSubscription(action: string, planId: string, properties: Record<string, any> = {}) {
    if (!planId) {
      console.warn('Plan ID is required for tracking subscription events');
      return;
    }

    this.trackEvent(`subscription_${action}`, {
      plan_id: planId,
      ...properties,
    });
  }

  /**
   * Track feature usage with enhanced context
   */
  trackFeatureUsage(featureName: string, properties: Record<string, any> = {}) {
    this.trackEvent('feature_used', {
      feature_name: featureName,
      ...properties,
    });
  }

  /**
   * Track errors with enhanced error context
   */
  trackError(error: Error, properties: Record<string, any> = {}) {
    this.trackEvent('error', {
      error_name: error.name,
      error_message: error.message,
      error_stack: error.stack,
      timestamp: new Date().toISOString(),
      ...properties,
    });
  }

  /**
   * Track performance metrics with validation
   */
  trackPerformance(metricName: string, value: number, properties: Record<string, any> = {}) {
    if (typeof value !== 'number' || isNaN(value)) {
      console.warn('Performance value must be a valid number');
      return;
    }

    this.trackEvent('performance_metric', {
      metric_name: metricName,
      value,
      timestamp: new Date().toISOString(),
      ...properties,
    });
  }

  /**
   * Reset user tracking with cleanup
   */
  reset() {
    if (!this.initialized) return;

    this.trackEvent('analytics_reset');
    amplitude.reset();
  }
}

export const analyticsService = new AnalyticsService();
