type EventProps = Record<string, any>;

/**
 * Analytics utility for tracking user interactions
 * This can be connected to any analytics service (Google Analytics, Mixpanel, etc.)
 */
export const analytics = {
  /**
   * Track a page view event
   */
  pageView: (url: string) => {
    if (typeof window === 'undefined') return;
    
    try {
      // Example: Google Analytics
      if (window.gtag) {
        window.gtag('config', process.env.NEXT_PUBLIC_GA_ID || '', {
          page_path: url,
        });
      }
      
      // You can add other analytics services here
      console.log(`[Analytics] Page view: ${url}`);
    } catch (error) {
      console.error('[Analytics] Error tracking page view:', error);
    }
  },
  
  /**
   * Track a custom event
   */
  trackEvent: (eventName: string, properties: EventProps = {}) => {
    if (typeof window === 'undefined') return;
    
    try {
      // Example: Google Analytics
      if (window.gtag) {
        window.gtag('event', eventName, properties);
      }
      
      // You can add other analytics services here
      console.log(`[Analytics] Event: ${eventName}`, properties);
    } catch (error) {
      console.error('[Analytics] Error tracking event:', error);
    }
  },
  
  /**
   * Track a conversion
   */
  trackConversion: (conversionId: string, value?: number, currency?: string) => {
    if (typeof window === 'undefined') return;
    
    try {
      // Example: Google Analytics
      if (window.gtag) {
        window.gtag('event', 'conversion', {
          send_to: `${process.env.NEXT_PUBLIC_GA_ID}/${conversionId}`,
          value,
          currency,
        });
      }
      
      console.log(`[Analytics] Conversion: ${conversionId}`, { value, currency });
    } catch (error) {
      console.error('[Analytics] Error tracking conversion:', error);
    }
  },
  
  /**
   * Track an error
   */
  trackError: (error: Error, properties: EventProps = {}) => {
    if (typeof window === 'undefined') return;
    
    try {
      // Example: Google Analytics
      if (window.gtag) {
        window.gtag('event', 'exception', {
          description: error.message,
          fatal: false,
          ...properties,
        });
      }
      
      console.error(`[Analytics] Error: ${error.message}`, properties);
    } catch (err) {
      console.error('[Analytics] Error tracking error event:', err);
    }
  },
};

// Type definitions for global window object
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
} 