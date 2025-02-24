import * as amplitude from '@amplitude/analytics-browser';

class AnalyticsService {
  private initialized = false;

  /**
   * Initialize Amplitude analytics
   */
  init() {
    if (this.initialized) return;

    amplitude.init(process.env.NEXT_PUBLIC_AMPLITUDE_API_KEY!, {
      defaultTracking: true,
      logLevel: process.env.NODE_ENV === 'production' ? amplitude.Types.LogLevel.None : amplitude.Types.LogLevel.Debug
    });

    this.initialized = true;
  }

  /**
   * Track a user event
   */
  trackEvent(eventName: string, properties?: Record<string, any>) {
    if (!this.initialized) this.init();
    amplitude.track(eventName, properties);
  }

  /**
   * Set user properties
   */
  setUserProperties(properties: Record<string, any>) {
    if (!this.initialized) this.init();
    amplitude.identify(new amplitude.Identify().setOnce(properties));
  }

  /**
   * Set user ID for tracking
   */
  setUserId(userId: string) {
    if (!this.initialized) this.init();
    amplitude.setUserId(userId);
  }

  /**
   * Track page view
   */
  trackPageView(pageName: string, properties?: Record<string, any>) {
    this.trackEvent('page_view', {
      page_name: pageName,
      ...properties
    });
  }

  /**
   * Track campaign events
   */
  trackCampaign(action: string, campaignId: string, properties?: Record<string, any>) {
    this.trackEvent(`campaign_${action}`, {
      campaign_id: campaignId,
      ...properties
    });
  }

  /**
   * Track email events
   */
  trackEmail(action: string, emailId: string, properties?: Record<string, any>) {
    this.trackEvent(`email_${action}`, {
      email_id: emailId,
      ...properties
    });
  }

  /**
   * Track subscription events
   */
  trackSubscription(action: string, planId: string, properties?: Record<string, any>) {
    this.trackEvent(`subscription_${action}`, {
      plan_id: planId,
      ...properties
    });
  }

  /**
   * Track feature usage
   */
  trackFeatureUsage(featureName: string, properties?: Record<string, any>) {
    this.trackEvent('feature_used', {
      feature_name: featureName,
      ...properties
    });
  }

  /**
   * Track errors
   */
  trackError(error: Error, properties?: Record<string, any>) {
    this.trackEvent('error', {
      error_name: error.name,
      error_message: error.message,
      error_stack: error.stack,
      ...properties
    });
  }

  /**
   * Track performance metrics
   */
  trackPerformance(metricName: string, value: number, properties?: Record<string, any>) {
    this.trackEvent('performance_metric', {
      metric_name: metricName,
      value,
      ...properties
    });
  }

  /**
   * Reset user tracking
   */
  reset() {
    if (!this.initialized) return;
    amplitude.reset();
  }
}

export const analyticsService = new AnalyticsService(); 