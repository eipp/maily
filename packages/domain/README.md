# Domain Package

This package contains domain models, types, and business logic that are shared across multiple services in the Maily platform.

## Purpose

The domain package provides:
- Shared domain entities and value objects
- Business logic that isn't service-specific
- Type definitions for core domain concepts
- Domain events and event handlers

## Organization

The package is organized by business domain rather than technical concerns:
- `campaigns/` - Campaign domain models and logic
- `contacts/` - Contact management domain models and logic
- `templates/` - Email template domain models and logic
- `auth/` - Authentication and authorization domain models
- `common/` - Shared primitives and utilities

## Usage

Services should import domain models and logic from this package rather than implementing them independently. This ensures consistency across services and prevents duplication.

```typescript
import { Campaign, CampaignStatus } from '@maily/domain/campaigns';
```

## Adding New Domain Concepts

When adding new domain concepts, consider:
1. Is this concept shared across multiple services?
2. Does it represent core business logic?
3. Is it stable and unlikely to change frequently?

If yes to these questions, it belongs in the domain package.