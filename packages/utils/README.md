# Maily Utilities Package

This package contains shared utility functions for the Maily platform.

## Utility Organization

The utilities in the Maily platform are organized into two main categories:

1. **Shared Utilities** (this package): Generic, reusable utility functions that are not specific to any particular feature or application.
2. **App-Specific Utilities**: Utility functions that are specific to a particular application or feature, located in `apps/{app}/utils/`.

## Directory Structure

```
packages/utils/
├── src/
│   ├── date/              # Date manipulation utilities
│   │   ├── format.ts
│   │   ├── parse.ts
│   │   └── index.ts
│   ├── string/            # String manipulation utilities
│   │   ├── format.ts
│   │   ├── validate.ts
│   │   └── index.ts
│   ├── array/             # Array manipulation utilities
│   ├── object/            # Object manipulation utilities
│   ├── validation/        # Validation utilities
│   ├── formatting/        # Formatting utilities
│   ├── network/           # Network request utilities
│   ├── storage/           # Storage utilities
│   ├── crypto/            # Cryptography utilities
│   ├── math/              # Math utilities
│   └── index.ts           # Main export file
├── package.json
└── tsconfig.json
```

## Usage Guidelines

### When to Use Shared Utilities

Use utilities from this package when:

1. The utility function is generic and reusable across multiple features.
2. The utility doesn't depend on application-specific state or logic.
3. The utility represents a common operation (date formatting, string manipulation, etc.).

### When to Create App-Specific Utilities

Create utilities in `apps/{app}/utils/` when:

1. The utility is specific to a particular feature or application.
2. The utility depends on application-specific state or logic.
3. The utility is only used within a single application.

## Utility Categories

The shared utilities are organized into these categories:

### Date Utilities

- `format`: Date formatting functions
- `parse`: Date parsing functions
- `diff`: Date difference calculations
- `timezone`: Timezone conversion utilities

### String Utilities

- `format`: String formatting functions
- `validate`: String validation functions
- `transform`: String transformation functions
- `sanitize`: String sanitization functions

### Array Utilities

- `sort`: Array sorting functions
- `filter`: Array filtering functions
- `transform`: Array transformation functions
- `group`: Array grouping functions

### Object Utilities

- `merge`: Object merging functions
- `diff`: Object difference functions
- `pick`: Object property selection functions
- `omit`: Object property omission functions

### Validation Utilities

- `email`: Email validation functions
- `url`: URL validation functions
- `phone`: Phone number validation functions
- `schema`: Schema validation utilities

### Formatting Utilities

- `number`: Number formatting functions
- `currency`: Currency formatting functions
- `percentage`: Percentage formatting functions
- `fileSize`: File size formatting functions

### Network Utilities

- `request`: HTTP request utilities
- `url`: URL manipulation utilities
- `params`: URL parameter utilities
- `headers`: HTTP header utilities

### Storage Utilities

- `localStorage`: Local storage utilities
- `sessionStorage`: Session storage utilities
- `cookie`: Cookie utilities
- `cache`: Caching utilities

## Best Practices

1. **Pure Functions**: Utilities should be pure functions without side effects.
2. **TypeScript**: All utilities should be properly typed with TypeScript.
3. **Documentation**: Each utility should have JSDoc comments explaining its purpose and parameters.
4. **Testing**: All utilities should have comprehensive tests.
5. **Performance**: Utilities should be optimized for performance.
6. **Size**: Utilities should be small and focused on a single responsibility.

## Contributing

When adding new utilities to this package:

1. Place the utility in the appropriate category directory.
2. Export the utility from the category's index.ts file.
3. Export the utility from the main index.ts file.
4. Add comprehensive tests for the utility.
5. Document the utility with JSDoc comments.
6. Update this README if adding a new category.
