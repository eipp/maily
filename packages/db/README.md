# Maily Database Package

The db package provides a unified database interface for Maily applications, built on Prisma ORM with PostgreSQL.

## Features

- **Prisma ORM Integration**: Type-safe database access with Prisma
- **Migration Management**: Automated database schema migrations
- **Seeding Utilities**: Easily populate databases with test or initial data
- **Query Builders**: Helpers for common query patterns
- **Transaction Support**: Manage database transactions
- **Connection Pooling**: Optimized database connection management
- **Multi-tenant Support**: Database isolation for multi-tenant applications
- **Audit Logging**: Track data changes in the database

## Installation

```bash
pnpm add @maily/db
```

## Usage

```typescript
import { db } from '@maily/db';

// Query the database
const users = await db.user.findMany({
  where: {
    orgId: 'org_123',
    isActive: true
  },
  include: {
    profile: true
  }
});

// Create a new record
const newCampaign = await db.campaign.create({
  data: {
    name: 'Welcome Series',
    orgId: 'org_123',
    status: 'DRAFT',
    emails: {
      create: [
        {
          subject: 'Welcome to Maily',
          content: '...',
          sendDelay: 0
        },
        {
          subject: 'Getting Started Guide',
          content: '...',
          sendDelay: 86400 // 1 day in seconds
        }
      ]
    }
  }
});

// Use transactions
const result = await db.$transaction(async (tx) => {
  const campaign = await tx.campaign.findUnique({
    where: { id: 'campaign_123' }
  });

  if (!campaign) throw new Error('Campaign not found');

  return tx.campaignSend.create({
    data: {
      campaignId: campaign.id,
      status: 'SCHEDULED',
      scheduledFor: new Date()
    }
  });
});
```

## Schema

The database schema is defined in `prisma/schema.prisma` and includes models for:

- **User**: User accounts and authentication
- **Organization**: Multi-tenant organization data
- **Team**: Team structure within organizations
- **Campaign**: Email campaigns and sequences
- **Email**: Email templates and content
- **Subscriber**: Email list subscribers
- **List**: Email subscriber lists
- **Tag**: Tags for segmentation
- **Segment**: Dynamic subscriber segments
- **Template**: Reusable email templates
- **CampaignSend**: Campaign sending history
- **EmailEvent**: Email delivery and engagement events

## Migrations

To run migrations:

```bash
# Generate a migration from schema changes
pnpm db:migrate:dev

# Apply migrations to production
pnpm db:migrate:deploy

# Reset the database (development only)
pnpm db:reset
```

## Seeding

Populate your database with initial data:

```bash
pnpm db:seed
```

## Dependencies

- prisma
- @prisma/client
- postgres
- zod
- @maily/config
