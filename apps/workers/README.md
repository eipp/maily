# Maily - apps/workers

This directory contains the workers module for the Maily platform. Workers handle background processing tasks such as email sending, analytics processing, and data archiving.

## Deployment

The workers are deployed as containerized services in the Maily infrastructure and are not directly accessible through a public domain. They communicate with other components through internal APIs and message queues.

## Worker Types

### Email Worker

The `email_worker.py` handles email processing and delivery tasks:

- **Email Sending**: Processes email sending requests and routes them to the appropriate email provider adapter
- **Delivery Tracking**: Tracks email delivery status and updates campaign metrics
- **Retry Logic**: Implements intelligent retry logic for failed email sends
- **Rate Limiting**: Ensures email sending respects provider rate limits
- **Personalization Processing**: Applies personalization to email templates before sending

### Analytics Worker

The `analytics_worker.py` processes campaign analytics data:

- **Event Processing**: Processes email events (opens, clicks, bounces, unsubscribes)
- **Metric Aggregation**: Aggregates metrics for campaigns and contacts
- **Performance Analysis**: Analyzes campaign performance and generates insights
- **AI-Powered Recommendations**: Generates recommendations for future campaigns
- **Trust Verification**: Prepares campaign metrics for blockchain verification

### Archiving Worker

The `archiving_worker.py` handles data archiving tasks:

- **Data Archiving**: Archives old campaign data to cold storage
- **Data Cleanup**: Removes unnecessary temporary data
- **Compliance Processing**: Ensures data retention policies are followed
- **Export Generation**: Generates data exports for user requests
- **Backup Management**: Manages database backups and restoration

### Canvas Worker

The `canvas.worker.ts` handles Canvas-related background processing:

- **State Synchronization**: Synchronizes Canvas state between clients
- **Rendering Optimization**: Pre-renders complex Canvas elements
- **Asset Processing**: Processes and optimizes assets used in Canvas
- **Collaboration Management**: Manages real-time collaboration sessions
- **State Persistence**: Persists Canvas state to the database

### Data Processor Worker

The `dataProcessor.worker.ts` handles data processing tasks:

- **Contact Import Processing**: Processes contact import files (CSV, Excel)
- **Data Transformation**: Transforms data between different formats
- **Data Validation**: Validates imported data against schema
- **Duplicate Detection**: Identifies and handles duplicate contacts
- **Enrichment Processing**: Processes contact enrichment requests

## Architecture

The workers follow the same hexagonal architecture principles as the rest of the platform:

- **Core Domain Logic**: Business logic independent of external dependencies
- **Adapter Pattern**: Consistent interfaces for external services
- **Message Queue Integration**: Workers consume tasks from message queues (Redis, RabbitMQ)
- **Observability**: Comprehensive logging, metrics, and tracing

## Development Philosophy

The workers are developed and maintained by a lean team consisting of a founder and an AI coding agent. This approach enables:

- **Autonomous Background Processing**: Workers operate with minimal human intervention
- **Self-Healing Systems**: Automatic recovery from failures and errors
- **Intelligent Scaling**: Dynamic resource allocation based on workload
- **Continuous Optimization**: AI-driven performance tuning and resource management
- **Comprehensive Monitoring**: Automated alerting and diagnostics

## Deployment

Workers are deployed as containerized services using Docker and Kubernetes:

- **Horizontal Scaling**: Workers can be scaled horizontally based on load
- **Resource Isolation**: Each worker type runs in its own container
- **Auto-scaling**: Kubernetes HPA for automatic scaling based on queue length
- **Graceful Shutdown**: Workers handle shutdown signals gracefully

## Development

To run workers locally:

```bash
# Python workers
cd apps/workers
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python email_worker.py

# TypeScript workers
cd apps/workers
npm install
npm run dev:canvas-worker
```

## Monitoring

Workers emit metrics and logs for monitoring:

- **Prometheus Metrics**: Task processing rates, error rates, queue lengths
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Tracing**: Distributed tracing with OpenTelemetry
- **Alerting**: Alerts for queue backlog, error rates, and worker health
