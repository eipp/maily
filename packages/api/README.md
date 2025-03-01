# Maily API Package

The API package provides a unified API layer for Maily applications, built with tRPC and Express. It serves as the backend interface for all Maily services.

## Features

- **tRPC Integration**: Type-safe API routes with end-to-end typings
- **Express Middleware**: API middleware for Express applications
- **Authentication**: Built-in authentication and authorization
- **Rate Limiting**: Request rate limiting for API endpoints
- **Validation**: Request validation with Zod schemas
- **Error Handling**: Standardized API error responses
- **Logging**: Request and response logging
- **Caching**: Response caching mechanisms
- **Pagination**: Standardized pagination for list endpoints
- **Filtering**: Query parameter filtering
- **Sorting**: Sorting capabilities for list endpoints
- **OpenAPI**: Automatic OpenAPI specification generation

## Installation

```bash
pnpm add @maily/api
```

## Usage

### Server-side Setup

```typescript
// server.ts
import express from 'express';
import { createApiRouter, createContext } from '@maily/api';

const app = express();

// Create API router
const apiRouter = createApiRouter({
  // API configuration options
  prefix: '/api',
  enableLogging: true,
  rateLimiting: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100 // limit each IP to 100 requests per windowMs
  }
});

// Add API routes to Express app
app.use(
  '/api',
  apiRouter.createExpressMiddleware({
    createContext
  })
);

// Start server
app.listen(3000, () => {
  console.log('Server started on http://localhost:3000');
});
```

### Client-side Usage

```typescript
// client.ts
import { createTRPCClient } from '@maily/api/client';

// Create API client
const api = createTRPCClient({
  url: 'http://localhost:3000/api'
});

// Example: Fetch campaigns
async function fetchCampaigns() {
  const campaigns = await api.campaigns.list.query({
    limit: 10,
    offset: 0,
    filter: {
      status: 'ACTIVE'
    },
    sort: {
      field: 'createdAt',
      order: 'desc'
    }
  });

  return campaigns;
}

// Example: Create a new campaign
async function createCampaign(data) {
  const campaign = await api.campaigns.create.mutate({
    name: data.name,
    description: data.description,
    // ...other campaign data
  });

  return campaign;
}
```

## API Routes

The API package provides the following route groups:

- **auth**: Authentication and user management
  - `signin`, `signup`, `signout`, `refreshToken`, `resetPassword`
- **campaigns**: Email campaign management
  - `list`, `get`, `create`, `update`, `delete`, `duplicate`, `schedule`, `pause`, `resume`
- **emails**: Email template management
  - `list`, `get`, `create`, `update`, `delete`, `preview`, `test`
- **subscribers**: Subscriber management
  - `list`, `get`, `create`, `update`, `delete`, `import`, `export`
- **lists**: Email list management
  - `list`, `get`, `create`, `update`, `delete`, `addSubscribers`, `removeSubscribers`
- **tags**: Tag management
  - `list`, `get`, `create`, `update`, `delete`, `assignToSubscribers`, `removeFromSubscribers`
- **segments**: Segment management
  - `list`, `get`, `create`, `update`, `delete`, `preview`
- **templates**: Email template management
  - `list`, `get`, `create`, `update`, `delete`, `preview`
- **organizations**: Organization management
  - `list`, `get`, `create`, `update`, `delete`, `invite`, `removeMember`
- **teams**: Team management
  - `list`, `get`, `create`, `update`, `delete`, `addMember`, `removeMember`
- **analytics**: Analytics data
  - `getDashboard`, `getCampaignStats`, `getEmailStats`, `getSubscriberGrowth`

## OpenAPI Documentation

Generate OpenAPI documentation for the API:

```bash
pnpm gen:openapi
```

This creates a `openapi.json` file that can be used with tools like Swagger UI or Redoc.

## Dependencies

- trpc
- express
- zod
- jose (for JWT)
- superjson
- cors
- @maily/db
- @maily/config
