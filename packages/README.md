# Maily Shared Packages

This directory contains shared packages that can be used across multiple services in the Maily platform.

## Package Structure

- `analytics/` - Analytics utilities and tracking
- `api-client/` - Typed API client for all Maily services
- `api/` - Shared API utilities
- `config/` - Shared configuration files and schemas
- `config-schema/` - Configuration schemas and validation
- `database/` - Database clients, migrations and shared models
  - `src/redis-client/` - Standardized Redis client for all services
- `domain/` - Domain models and business logic
- `email-renderer/` - Email rendering utilities
- `error-handling/` - Standardized error handling
- `eslint-config-maily/` - Shared ESLint configuration
- `feature-flags/` - Feature flag management
- `testing/` - Testing utilities and fixtures
- `ui-components/` - Shared UI components
- `ui/` - UI utilities and hooks
- `utils/` - General purpose utilities

## Usage Guidelines

- All services should import shared code from these packages rather than duplicating functionality
- Each package should have a clear, single responsibility
- Packages should have minimal dependencies on other packages
- Each package should include a README with usage examples
- Follow the dependency structure in package.json for proper dependency management

## Standardization

As part of our repository improvement efforts, we have:

1. Standardized naming conventions (kebab-case for directories, camelCase for files)
2. Consolidated duplicate implementations
3. Created compatibility modules for backward compatibility
4. Improved documentation and examples

## Package Development

When creating or updating packages:

1. Use TypeScript for all JavaScript packages
2. Include proper type definitions
3. Write comprehensive tests
4. Document the public API
5. Follow the established naming conventions
6. Ensure backward compatibility or provide migration guides