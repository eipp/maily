# Maily API Reference

## Overview

The Maily API provides programmatic access to email marketing functionality with a REST-based design. It uses standard HTTP verbs, returns JSON responses, includes resource-oriented URLs, and uses HTTP status codes to indicate errors.

## Authentication

Three authentication methods are supported:

1. **API Keys**: Include in request header as `X-API-Key: your_api_key_here`
2. **JWT Authentication**: Include as `Authorization: Bearer YOUR_JWT_TOKEN`
3. **OAuth 2.0**: For user authorization flows

## Base URL

All API requests should be made to:

```
https://api.maily.io/api/v1/
```

## Key Endpoints

### Email Operations

- `POST /v1/send-email` - Send an email
- `GET /v1/email-status/{emailId}` - Get email status

### Campaign Management

- `GET /campaigns` - List campaigns
- `POST /campaigns` - Create a campaign
- `GET /campaigns/{id}` - Get campaign details
- `PATCH /campaigns/{id}` - Update a campaign
- `DELETE /campaigns/{id}` - Delete a campaign

### Subscribers

- `GET /subscribers` - List subscribers
- `POST /subscribers` - Create a subscriber
- `GET /subscribers/{id}` - Get subscriber details
- `PATCH /subscribers/{id}` - Update a subscriber
- `DELETE /subscribers/{id}` - Delete a subscriber
- `POST /subscribers/import` - Bulk import subscribers

### Lists

- `GET /lists` - List subscriber lists
- `POST /lists` - Create a list
- `GET /lists/{id}` - Get list details
- `PATCH /lists/{id}` - Update a list
- `DELETE /lists/{id}` - Delete a list
- `GET /lists/{id}/subscribers` - Get list subscribers

### Analytics

- `GET /analytics/campaigns` - Campaign performance metrics
- `GET /analytics/lists` - List growth and engagement
- `GET /analytics/subscribers` - Subscriber engagement
- `GET /analytics/overview` - Account-wide dashboard

### AI Features

- `POST /ai/generate-subject` - Generate email subject lines
- `POST /ai/generate-content` - Generate email content
- `POST /ai/analyze-content` - Analyze content for deliverability

## Request Format

For `POST`, `PUT`, and `PATCH` requests, the request body should be valid JSON:

```json
{
  "name": "Campaign Name",
  "subject": "Email Subject",
  "content": {
    "html": "<html><body><h1>Content</h1></body></html>",
    "text": "Plain text content"
  }
}
```

## Response Format

All API responses are returned in JSON format:

```json
{
  "data": {
    "id": "camp_1a2b3c4d5e",
    "name": "Campaign Name",
    "subject": "Email Subject",
    "status": "draft",
    "created_at": "2025-03-01T12:00:00Z"
  },
  "meta": {
    "request_id": "req_1234567890"
  }
}
```

For collection endpoints, responses include pagination information:

```json
{
  "data": [...],
  "meta": {
    "pagination": {
      "total": 42,
      "count": 10,
      "per_page": 10,
      "current_page": 1,
      "total_pages": 5,
      "links": {
        "next": "https://api.maily.io/api/v1/campaigns?page=2"
      }
    }
  }
}
```

## Error Handling

The API uses HTTP status codes to indicate the result of requests:

| Code | Description |
|------|-------------|
| 200 | OK - The request was successful |
| 201 | Created - The resource was successfully created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication failed |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Request cannot be processed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

Error responses follow this format:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "The provided campaign name is too long",
    "details": [
      {
        "field": "name",
        "message": "Must be less than 100 characters"
      }
    ]
  },
  "meta": {
    "request_id": "req_1234567890"
  }
}
```

## Rate Limits

| Plan | Rate Limit | Burst Limit |
|------|------------|-------------|
| Free | 60 requests/minute | 100 requests/minute |
| Standard | 180 requests/minute | 300 requests/minute |
| Premium | 600 requests/minute | 1000 requests/minute |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 180
X-RateLimit-Remaining: 179
X-RateLimit-Reset: 1614556800
