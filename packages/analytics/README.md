# Maily Analytics Package

The analytics package provides tracking, reporting, and visualization tools for email campaign performance and user engagement.

## Features

- **Event Tracking**: Track user interactions and campaign performance
- **Analytics Dashboard**: Visualize campaign metrics with charts and reports
- **Data Export**: Export analytics data in various formats (CSV, JSON, Excel)
- **Custom Metrics**: Define and track custom metrics for campaigns
- **Segmentation**: Analyze performance across different user segments
- **Integration**: Connect with external analytics platforms (Google Analytics, Mixpanel, etc.)

## Installation

```bash
pnpm add @maily/analytics
```

## Usage

```typescript
import { trackEvent, getMetrics } from '@maily/analytics';

// Track a campaign open event
trackEvent('campaign_open', {
  campaignId: 'campaign-123',
  userId: 'user-456',
  timestamp: new Date(),
});

// Get campaign metrics
const metrics = await getMetrics('campaign-123');
console.log(metrics);
```

## API Reference

See the [Technical Reference](../../docs/technical-reference.md) for detailed API documentation.

## Configuration

The analytics package can be configured through environment variables or the config package:

```typescript
import { configureAnalytics } from '@maily/analytics';

configureAnalytics({
  endpoint: process.env.ANALYTICS_ENDPOINT,
  apiKey: process.env.ANALYTICS_API_KEY,
  sampleRate: 0.1, // Sample 10% of events
  batchSize: 10,
  flushInterval: 30000, // 30 seconds
});
```

## Dependencies

- @maily/config
- @maily/utils
