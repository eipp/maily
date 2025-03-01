# Analytics Service

A microservice responsible for collecting, processing, and analyzing event data from the Maily platform. This service follows an event-driven architecture to handle high-throughput analytics data.

## Features

- **Event Collection API**: REST API for tracking user events and actions
- **Event Processing Engine**: Processes and enriches incoming events
- **Real-time Metrics**: Generate and update metrics in real-time
- **Data Aggregation**: Aggregate analytics data across different dimensions
- **Caching Layer**: Redis-based caching for high-performance queries
- **Event-Driven Architecture**: Uses RabbitMQ for asynchronous event processing
- **Monitoring & Observability**: Built-in Prometheus metrics and logging

## Architecture

The Analytics Service is built using a clean architecture approach:

- **API Layer**: RESTful API for event tracking and data retrieval
- **Event Processor**: Processes incoming events and updates metrics
- **Storage Layer**: MongoDB for event storage and aggregated metrics
- **Cache Layer**: Redis for caching frequent queries and metrics
- **Message Broker**: RabbitMQ for handling event streams
- **Monitoring**: Prometheus metrics for observability

## API Endpoints

### Event Tracking

- `POST /api/v1/events` - Track a single event
- `POST /api/v1/events/batch` - Track multiple events in batch

### Data Retrieval

- `GET /api/v1/events` - Get events with filtering options
- `GET /api/v1/events/:id` - Get a specific event by ID
- `GET /api/v1/events/counts` - Get event counts by type

## Event Schema

```typescript
interface EventMessage {
  id: string;            // Unique event identifier
  type: string;          // Event type identifier
  data: any;             // Event data payload
  timestamp: Date;       // Event timestamp
  source: string;        // Source of the event
  correlationId?: string; // Optional correlation ID for tracing
  metadata?: Record<string, any>; // Optional metadata
}
```

## Getting Started

### Prerequisites

- Node.js v18.x or higher
- MongoDB v6.x
- Redis v7.x
- RabbitMQ v3.11

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   cd apps/analytics-service
   npm install
   ```
3. Create a `.env` file based on `.env.example`
4. Run the development server:
   ```bash
   npm run dev
   ```

### Using Docker Compose

The easiest way to run the service with all its dependencies is using Docker Compose:

```bash
cd apps/analytics-service
docker-compose up -d
```

This will start:
- Analytics Service
- MongoDB
- Redis
- RabbitMQ
- Prometheus (metrics)
- Grafana (dashboards)

### Environment Variables

Key environment variables:

- `NODE_ENV` - Environment (development, production, test)
- `PORT` - HTTP port (default: 4000)
- `MONGODB_URI` - MongoDB connection string
- `REDIS_HOST` - Redis host
- `RABBITMQ_URL` - RabbitMQ connection URL
- `ENABLE_METRICS` - Enable Prometheus metrics

See `.env.example` for a complete list of configuration options.

## Development

### Running Tests

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Test coverage
npm run test:coverage
```

### Building for Production

```bash
npm run build
```

## Monitoring & Observability

The service exposes metrics at `/metrics` endpoint in Prometheus format. Key metrics include:

- HTTP request latency and counts
- Event processing latency
- Queue sizes and processing rates
- Cache hit/miss rates
- Database operation metrics
