# Email Service

A scalable, reliable, and provider-agnostic email delivery service for JustMaily, built with TypeScript and Node.js following hexagonal architecture principles. Designed to be maintained by our lean team (founder + AI agent).

## Features

- **Provider Agnostic**: Supports multiple email providers (Resend, SendGrid, Mailgun) through a unified interface
- **Scalable Architecture**: Designed to handle high volume email delivery with Kubernetes auto-scaling
- **Rate Limiting**: Configurable rate limits to prevent abuse and stay within provider limits
- **Comprehensive Metrics**: Detailed metrics for monitoring email delivery performance
- **Templating Support**: Create, manage, and render email templates
- **Bulk Sending**: Efficient handling of bulk email operations
- **Delivery Tracking**: Monitor email delivery status
- **REST API**: Clean REST API for integration with other services

## JustMaily Domain Integration

This service seamlessly integrates with all JustMaily domains:

- **justmaily.com** - Main landing page and website
- **app.justmaily.com** - The main JustMaily application
- **console.justmaily.com** - Developer console and API access

## Architecture

The email service follows a hexagonal architecture (also known as ports and adapters) to ensure separation of concerns and maintainability:

```
src/
├── domain/             # Domain layer - core business models and interfaces
│   ├── models.ts       # Domain entities (Email, Template, etc.)
│   └── interfaces.ts   # Domain interfaces (EmailProvider, EmailRepository, etc.)
│
├── application/        # Application layer - business logic and use cases
│   └── usecases/
│       └── email-service.ts  # Main service implementation
│
├── infrastructure/     # Infrastructure layer - external dependencies
│   ├── entities/       # Database entities
│   ├── metrics/        # Metrics implementation
│   ├── rate-limiting/  # Rate limiting implementation
│   └── repositories/   # Database repositories
│
└── adapters/           # Adapters layer - connections to the outside world
    ├── api/            # REST API
    ├── factories/      # Factory for creating providers
    └── providers/      # Email provider implementations
```

## AI-Optimized Development

This repository is structured to facilitate AI-assisted development:
- Clear code organization and consistent patterns
- Comprehensive type definitions
- Detailed comments for AI understanding

## Getting Started

### Prerequisites

- Node.js 18 or higher
- PostgreSQL database
- Redis (for rate limiting)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   cd apps/email-service
   npm install
   ```
3. Copy the environment example file:
   ```
   cp env.example .env
   ```
4. Update the environment variables with your configuration
5. Build the application:
   ```
   npm run build
   ```

### Running Locally

```
npm start
```

For development with hot reloading:

```
npm run dev
```

### Configuration

The service uses environment variables for configuration. For domain-specific settings, ensure you set the appropriate CORS domains in the environment variables.

### Running with Docker

```
cd apps/email-service
docker build -t email-service .
docker run -p 8080:8080 --env-file .env email-service
```

### Deploying to Kubernetes

1. Create the necessary secrets:
   ```
   kubectl create secret generic email-service-secrets \
     --from-literal=db_username=your_db_username \
     --from-literal=db_password=your_db_password \
     --from-literal=email_provider_api_key=your_api_key
   ```

2. Apply the Kubernetes configuration:
   ```
   kubectl apply -f kubernetes/deployment.yaml
   kubectl apply -f kubernetes/hpa.yaml
   ```

## API Endpoints

### Email Operations

- `POST /api/emails/send` - Send a single email
- `POST /api/emails/send-bulk` - Send multiple emails in bulk
- `GET /api/emails/status/:messageId` - Get email delivery status

### Template Operations

- `GET /api/emails/templates/:templateId` - Get a template
- `POST /api/emails/templates` - Create a template
- `PUT /api/emails/templates/:templateId` - Update a template
- `DELETE /api/emails/templates/:templateId` - Delete a template
- `POST /api/emails/templates/:templateId/render` - Render a template with variables

### Monitoring

- `GET /metrics` - Prometheus metrics endpoint
- `GET /api/emails/health` - Health check endpoint

## Environment Variables

See the `env.example` file for a complete list of supported environment variables.

## Metrics

The service exposes the following Prometheus metrics:

- `email_send_total` - Counter of emails sent (labels: provider, template, status)
- `email_send_duration_seconds` - Histogram of email sending duration (labels: provider)
- `email_delivery_total` - Counter of email delivery status updates (labels: provider, status)
- `email_provider_error_total` - Counter of provider errors (labels: provider, error_type)

### Viewing Metrics

Access the metrics dashboard at `console.justmaily.com/metrics` when deployed in production.

## Rate Limiting

Rate limiting is implemented with Redis and can be configured per provider using the following environment variables:

- `RATE_LIMIT_RESEND` - Daily limit for Resend
- `RATE_LIMIT_SENDGRID` - Daily limit for SendGrid
- `RATE_LIMIT_MAILGUN` - Daily limit for Mailgun

## Adding a New Provider

To add a new email provider:

1. Create a new provider implementation in `src/adapters/providers/`
2. Implement the `EmailProvider` interface
3. Update the `ProviderType` and `EmailProviderFactory` to include the new provider

## Domain Configurations

When integrating with domains:

```typescript
// Example domain configuration in environment variables
CORS_DOMAINS=justmaily.com,app.justmaily.com,console.justmaily.com
APP_DOMAIN=app.justmaily.com
CONSOLE_DOMAIN=console.justmaily.com
```

## Testing

Run tests with:

```
cd apps/email-service
npm test
```

```
npm test
```

## License

MIT
