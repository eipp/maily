# Maily API Overview

The Maily API provides programmatic access to the Maily platform, allowing you to integrate Maily with your applications and services.

## API Endpoints

The API is organized around RESTful principles and uses standard HTTP verbs and status codes. All endpoints return JSON responses.

### Base URL

```
https://api.maily.com/v1
```

## Authentication

All API requests require authentication. The Maily API uses API keys for authentication. To obtain an API key, visit the [API Settings](https://app.maily.com/settings/api) page in the Maily dashboard.

API keys should be included in the `Authorization` header of each request:

```
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

The API enforces rate limiting to ensure fair usage. Rate limits are applied per API key and vary by endpoint. Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1614556800
```

If you exceed the rate limit, you will receive a `429 Too Many Requests` response.

## Pagination

List endpoints support pagination using the `limit` and `offset` query parameters:

```
GET /v1/campaigns?limit=10&offset=0
```

Pagination information is included in the response:

```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "limit": 10,
    "offset": 0,
    "next": "/v1/campaigns?limit=10&offset=10",
    "prev": null
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request. In case of an error, the response body will contain an error object with additional information:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "The request parameter 'name' is missing",
    "details": {
      "parameter": "name"
    },
    "trace_id": "1a2b3c4d5e6f"
  }
}
```

## API Versioning

The API is versioned to ensure backward compatibility. The current version is `v1`. The version is included in the URL path.

## API Explorer

You can explore the API using our interactive API Explorer at [https://api.maily.com/explorer](https://api.maily.com/explorer).

## SDKs and Client Libraries

We provide official SDKs for the following languages:

- [JavaScript/TypeScript](https://github.com/mailyapp/maily-js)
- [Python](https://github.com/mailyapp/maily-python)
- [Ruby](https://github.com/mailyapp/maily-ruby)
- [PHP](https://github.com/mailyapp/maily-php)
- [Go](https://github.com/mailyapp/maily-go)

## API Reference

For detailed information about each endpoint, see the [API Reference](./endpoints.md).