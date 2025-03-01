/**
 * Performance monitoring client for tracking Core Web Vitals and custom metrics
 * This module provides tools for collecting real user metrics (RUM) and sending
 * them to our analytics backend.
 */
import { getLCP, getFID, getCLS, getFCP, getTTFB } from 'web-vitals';
import { v4 as uuidv4 } from 'uuid';

// Types for metrics
interface PerformanceMetric {
  name: string;
  value: number;
  id: string;
  // Additional properties based on what web-vitals provides
  delta?: number;
  rating?: 'good' | 'needs-improvement' | 'poor';
  navigationType?: string;
}

interface CustomMetric {
  name: string;
  value: number;
  context?: Record<string, any>;
}

interface SendMetricOptions {
  endpoint?: string;
  useBeacon?: boolean;
  debug?: boolean;
  sampleRate?: number; // 0-1, percentage of sessions to track (0.1 = 10%)
}

// Default configuration
const DEFAULT_CONFIG: SendMetricOptions = {
  endpoint: '/api/vitals',
  useBeacon: true,
  debug: false,
  sampleRate: 0.1, // Track 10% of sessions by default
};

// Unique session ID for grouping metrics
const SESSION_ID = uuidv4();

// Sample session based on rate
let IS_SAMPLED_SESSION = false;

/**
 * Determines if the current session should be sampled based on the sample rate
 */
function shouldSampleSession(sampleRate: number = 0.1): boolean {
  return Math.random() < sampleRate;
}

/**
 * Sends performance metrics to the analytics endpoint
 */
function sendMetricToAnalytics(
  metric: PerformanceMetric,
  options: SendMetricOptions = DEFAULT_CONFIG
): void {
  // Skip if this session isn't sampled
  if (!IS_SAMPLED_SESSION) {
    return;
  }

  const { endpoint, useBeacon, debug } = { ...DEFAULT_CONFIG, ...options };

  // Prepare data payload
  const body = JSON.stringify({
    ...metric,
    page: window.location.pathname,
    referrer: document.referrer || '',
    userAgent: navigator.userAgent,
    timestamp: Date.now(),
    sessionId: SESSION_ID,
    // Include connection info if available
    connection: navigator.connection ? {
      effectiveType: (navigator.connection as any).effectiveType,
      downlink: (navigator.connection as any).downlink,
      rtt: (navigator.connection as any).rtt,
      saveData: (navigator.connection as any).saveData,
    } : undefined,
    // Device information
    device: {
      screenWidth: window.screen.width,
      screenHeight: window.screen.height,
      devicePixelRatio: window.devicePixelRatio,
    },
  });

  // Log to console in debug mode
  if (debug) {
    console.info('📊 Performance metric:', metric.name, metric.value);
  }

  // Use Navigator.sendBeacon for more reliable sending during page unload
  if (useBeacon && navigator.sendBeacon) {
    navigator.sendBeacon(endpoint!, body);
  } else {
    // Fallback to fetch API
    fetch(endpoint!, {
      body,
      method: 'POST',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json'
      }
    }).catch(err => {
      if (debug) {
        console.error('Failed to send performance metric:', err);
      }
    });
  }
}

/**
 * Sends a custom performance metric to analytics
 */
export function trackCustomMetric(name: string, value: number, context: Record<string, any> = {}): void {
  if (!IS_SAMPLED_SESSION) {
    return;
  }

  sendMetricToAnalytics({
    name,
    value,
    id: `${name}-${Date.now()}`,
    context
  } as any);
}

/**
 * Marks a performance milestone that can be used for measuring duration between points
 */
export function markPerformanceMilestone(name: string): void {
  if (!IS_SAMPLED_SESSION) {
    return;
  }

  if (window.performance && window.performance.mark) {
    window.performance.mark(name);
  }
}

/**
 * Measures time between two performance marks and reports it
 */
export function measurePerformance(name: string, startMark: string, endMark: string): void {
  if (!IS_SAMPLED_SESSION || !window.performance || !window.performance.measure) {
    return;
  }

  try {
    // Create the performance measure
    window.performance.measure(name, startMark, endMark);

    // Get the measurement
    const measures = window.performance.getEntriesByName(name, 'measure');
    if (measures.length > 0) {
      trackCustomMetric(name, measures[0].duration);
    }
  } catch (e) {
    console.error('Error measuring performance:', e);
  }
}

/**
 * Initialize the time to interactive polyfill and track it
 */
async function trackTimeToInteractive(): Promise<void> {
  try {
    // Dynamically import the TTI polyfill
    const { getFirstConsistentlyInteractive } = await import('tti-polyfill');
    getFirstConsistentlyInteractive().then(tti => {
      if (tti) {
        sendMetricToAnalytics({
          name: 'TTI',
          value: tti,
          id: `TTI-${Date.now()}`
        });
      }
    });
  } catch (e) {
    console.error('Failed to load TTI polyfill:', e);
  }
}

/**
 * Track first paint and first contentful paint from performance timeline
 */
function trackPaintTimings(): void {
  if (window.performance && window.performance.getEntriesByType) {
    const paintMetrics = performance.getEntriesByType('paint');
    for (const paintMetric of paintMetrics) {
      sendMetricToAnalytics({
        name: paintMetric.name,
        value: paintMetric.startTime,
        id: `${paintMetric.name}-${Date.now()}`
      });
    }
  }
}

/**
 * Track largest contentful paint elements for debugging
 */
function trackLargestContentfulPaintElement(): void {
  new PerformanceObserver((entryList) => {
    for (const entry of entryList.getEntries()) {
      // Track additional details about the LCP element
      const lcpEntry = entry as any; // PerformanceEventTiming doesn't match the LCP types
      if (lcpEntry.element) {
        trackCustomMetric('LCP_Element', lcpEntry.startTime, {
          elementType: lcpEntry.element.tagName,
          elementId: lcpEntry.element.id,
          elementClass: lcpEntry.element.className,
          elementSize: lcpEntry.size,
          elementUrl: lcpEntry.url,
        });
      }
    }
  }).observe({ type: 'largest-contentful-paint', buffered: true });
}

/**
 * Track long tasks to identify JavaScript execution issues
 */
function trackLongTasks(): void {
  if (!('PerformanceObserver' in window)) return;

  try {
    new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        trackCustomMetric('LongTask', entry.duration, {
          startTime: entry.startTime,
          duration: entry.duration,
          taskName: entry.name,
        });
      }
    }).observe({ type: 'longtask', buffered: true });
  } catch (e) {
    console.error('Long tasks monitoring not supported', e);
  }
}

/**
 * Track resource loading performance (scripts, CSS, images, etc.)
 */
function trackResourcePerformance(): void {
  if (!('PerformanceObserver' in window)) return;

  try {
    new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        // Only track resources that take longer than 200ms to load
        if (entry.duration > 200) {
          const resource = entry as PerformanceResourceTiming;
          trackCustomMetric(`Resource_${getResourceType(resource.name)}`, resource.duration, {
            url: resource.name,
            initiatorType: resource.initiatorType,
            transferSize: resource.transferSize,
            decodedBodySize: resource.decodedBodySize,
            encodedBodySize: resource.encodedBodySize,
          });
        }
      }
    }).observe({ type: 'resource', buffered: true });
  } catch (e) {
    console.error('Resource performance monitoring not supported', e);
  }
}

/**
 * Get the type of resource based on file extension or URL pattern
 */
function getResourceType(url: string): string {
  if (/\.js(\?|$)/.test(url)) return 'JS';
  if (/\.css(\?|$)/.test(url)) return 'CSS';
  if (/\.(png|jpg|jpeg|gif|webp|svg)(\?|$)/.test(url)) return 'Image';
  if (/\.(woff|woff2|ttf|otf)(\?|$)/.test(url)) return 'Font';
  if (/\.(mp4|webm|ogv)(\?|$)/.test(url)) return 'Video';
  return 'Other';
}

/**
 * Initialize performance monitoring
 */
export function initPerformanceMonitoring(options: SendMetricOptions = {}): void {
  const config = { ...DEFAULT_CONFIG, ...options };

  // Determine if this session should be sampled
  IS_SAMPLED_SESSION = shouldSampleSession(config.sampleRate);

  // Skip initialization if this session isn't sampled
  if (!IS_SAMPLED_SESSION) {
    return;
  }

  // Core Web Vitals
  getCLS(metric => sendMetricToAnalytics(metric, config));
  getFID(metric => sendMetricToAnalytics(metric, config));
  getLCP(metric => sendMetricToAnalytics(metric, config));
  getFCP(metric => sendMetricToAnalytics(metric, config));
  getTTFB(metric => sendMetricToAnalytics(metric, config));

  // Advanced metrics
  trackTimeToInteractive();

  // Add load event listener
  window.addEventListener('load', () => {
    // These metrics are only available after load
    trackPaintTimings();

    // Track time from navigation start to load event
    const loadTime = performance.now();
    trackCustomMetric('LoadTime', loadTime);

    // Defer non-critical monitoring
    setTimeout(() => {
      trackLargestContentfulPaintElement();
      trackLongTasks();
      trackResourcePerformance();
    }, 0);
  });

  // Track page visibility changes (useful for understanding user engagement)
  document.addEventListener('visibilitychange', () => {
    trackCustomMetric('VisibilityChange', performance.now(), {
      state: document.visibilityState
    });
  });

  // Log initialization
  if (config.debug) {
    console.info('📊 Performance monitoring initialized', {
      sessionId: SESSION_ID,
      endpoint: config.endpoint
    });
  }
}

// Export default configuration
export const PerformanceConfig = DEFAULT_CONFIG;
