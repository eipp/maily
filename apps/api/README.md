# Maily - apps/api

This directory contains the API module for the Maily platform. It's built with FastAPI and uses SQLAlchemy ORM for database interactions.

## Technologies

- Python 3.10+
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- OctoTools for AI orchestration
- Redis for caching and rate limiting
- Support for multiple email providers (Resend, SendGrid, Mailgun)

## Structure

- `ai/`: OctoTools integration and AI model adapters
- `models/`: Database models and schema definitions
- `routers/`: API route definitions
- `services/`: Business logic and service layer
- `database/`: Database connection and ORM configuration
- `middleware/`: Request/response middleware
- `errors/`: Error handling utilities
- `tests/`: Unit and integration tests
- `workers/`: Background processing workers
- `platforms/`: Email platform adapters (Resend, SendGrid, Mailgun)

## Deployment

The API is deployed at **api.justmaily.com** and serves as the backend for the Maily platform. API documentation is available at **console.justmaily.com**.

## Hexagonal Architecture

The API follows hexagonal architecture principles, with a clear separation between domain logic and external dependencies. This is implemented through the adapter pattern, which provides a consistent interface for interacting with external services.

### Adapter Pattern Implementation

The adapter pattern is fully implemented in the following areas:

1. **AI Model Adapters**: Located in `ai/adapters/`, these provide a consistent interface for interacting with different AI providers (OpenAI, Anthropic, Google).

2. **Email Provider Adapters**: Located in `platforms/`, these provide a consistent interface for sending emails through different providers (Resend, SendGrid, Mailgun).

3. **Storage Adapters**: Provide a consistent interface for storing files and data in different storage systems.

For more details on the adapter pattern implementation, see the [AI Adapters Documentation](../../docs/ai-adapters.md).

## Standardized API

The API follows a standardized RESTful design with consistent endpoint patterns and response formats:

### Response Format

All API responses follow a standardized format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "requestId": "req_123456",
    "timestamp": "2023-07-15T12:34:56Z"
  }
}
```

For error responses:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "invalid_request",
    "message": "The request was invalid",
    "details": { ... }
  },
  "meta": {
    "requestId": "req_123456",
    "timestamp": "2023-07-15T12:34:56Z"
  }
}
```

### Endpoint Structure

Endpoints follow a consistent structure:

- Resource collections: `/v1/{resource}` (e.g., `/v1/campaigns`)
- Resource instances: `/v1/{resource}/{id}` (e.g., `/v1/campaigns/camp_123`)
- Resource actions: `/v1/{resource}/{id}/{action}` (e.g., `/v1/campaigns/camp_123/schedule`)

For complete API documentation, see the [API Documentation](../../docs/api/api-documentation.md) or visit [console.justmaily.com](https://console.justmaily.com).

## AI Integration

The API integrates with OctoTools for AI orchestration, supporting multiple AI providers through adapter patterns. See the `ai/` directory for implementation details.

## Authentication

Maily API implements a robust authentication system that supports multiple authentication methods:

### JWT Authentication

JWT authentication is implemented using Auth0 as the identity provider. To authenticate with JWT:

1. Include the JWT token in the `Authorization` header of API requests:
   ```
   Authorization: Bearer <jwt_token>
   ```

2. The authentication middleware will validate the JWT token and extract user information.

### API Key Authentication

API key authentication is implemented for programmatic access to the API. To authenticate with an API key:

1. Generate an API key using the API key endpoints
2. Include the API key in the `X-API-Key` header of API requests:
   ```
   X-API-Key: maily_<api_key>
   ```

3. The authentication middleware will validate the API key and retrieve the associated user.

### API Key Endpoints

The following endpoints are available for API key management:

- `POST /api-keys`: Create a new API key
  ```json
  {
    "name": "My API Key",
    "expires_at": "2025-12-31T23:59:59Z"  // Optional
  }
  ```

- `GET /api-keys`: List all API keys for the current user

- `DELETE /api-keys/{api_key_id}`: Revoke an API key

### Authentication Middleware

The authentication middleware is implemented in `middleware/auth_middleware.py` and provides the following dependencies:

- `get_current_user`: Requires authentication (JWT or API key) and returns the current user
- `require_admin`: Requires the current user to have admin privileges
- `optional_auth`: Optional authentication, returns the current user if authenticated, otherwise None

For more detailed information about the authentication system, refer to the [Authentication Documentation](../../docs/authentication.md).

## Rate Limiting

The API implements rate limiting to prevent abuse and ensure fair usage. Rate limits are applied per API key and are configurable based on the user's subscription tier.

Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1626355496
```

## Webhooks

The API supports webhooks for event-driven integration. Webhook events include:

- Campaign events: `campaign.sent`, `campaign.delivered`
- Email events: `email.opened`, `email.clicked`, `email.bounced`, `email.unsubscribed`
- Contact events: `contact.created`, `contact.updated`

For more information on webhooks, see the [API Documentation](../../docs/api/api-documentation.md#webhooks).

## Development Philosophy

The API is developed and maintained by a lean team consisting of a founder and an AI coding agent. This approach enables:

- **Rapid API Evolution**: Quick adaptation to changing requirements and new features
- **Consistent Implementation**: AI-enforced coding standards and patterns
- **Comprehensive Documentation**: Automated API documentation generation and maintenance
- **Efficient Problem Solving**: AI-assisted debugging and optimization
- **Scalable Architecture**: Design patterns that facilitate growth without proportional team expansion

## Development

To run the API locally:

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at http://localhost:8000. The interactive API documentation is available at http://localhost:8000/docs.
