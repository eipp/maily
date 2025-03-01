# Maily Web Application Utilities

This directory contains app-specific utility functions for the Maily web application.

## Utility Organization

The utilities in this directory are organized by feature or domain:

```
utils/
├── auth/                  # Authentication-related utilities
├── api/                   # API interaction utilities
├── canvas/                # Email canvas editor utilities
├── formatting/            # App-specific formatting utilities
├── validation/            # App-specific validation utilities
├── storage/               # App-specific storage utilities
├── analytics/             # Analytics-related utilities
└── ai/                    # AI feature utilities
```

## When to Create Utilities Here

Create utilities in this directory when:

1. The utility is specific to the Maily web application
2. The utility depends on application-specific state or logic
3. The utility is only used within the web application

## When to Use Shared Utilities

For generic, reusable utility functions that are not specific to the Maily web application, use utilities from the `packages/utils` package.

## Utility Structure

Each utility file should:

1. Export named functions
2. Include TypeScript type definitions
3. Include JSDoc comments
4. Be focused on a specific domain or feature

Example:

```typescript
/**
 * Formats a campaign name according to Maily's naming conventions
 * @param name - The raw campaign name
 * @param date - Optional date to append to the name
 * @returns Formatted campaign name
 */
export function formatCampaignName(name: string, date?: Date): string {
  // Implementation
}
```

## Canvas Utilities

Canvas utilities for the email editor should:

1. Handle fabric.js object manipulations
2. Provide helper functions for canvas operations
3. Follow the patterns established in the Canvas components

## API Utilities

API utilities should:

1. Use the fetch API or axios for HTTP requests
2. Handle error cases appropriately
3. Provide type-safe wrappers around API endpoints
4. Include proper authentication handling

## Authentication Utilities

Authentication utilities should:

1. Handle token management
2. Provide user session utilities
3. Include permission and role checking functions
4. Follow security best practices

## Testing

All utilities should have tests that:

1. Verify the utility functions correctly
2. Test edge cases
3. Mock external dependencies

## Best Practices

1. **Pure Functions**: Utilities should be pure functions without side effects when possible.
2. **TypeScript**: All utilities should be properly typed with TypeScript.
3. **Documentation**: Each utility should have JSDoc comments explaining its purpose and parameters.
4. **Error Handling**: Utilities should handle errors gracefully.
5. **Performance**: Utilities should be optimized for performance.
6. **Size**: Utilities should be small and focused on a single responsibility.
