# Next.js Configuration Standardization

This document explains the standardization of Next.js configuration for the Maily web application.

## Configuration Decision

We have standardized on a single Next.js configuration file using the ES modules format (`.mjs`). The configuration is located at:

```
apps/web/next.config.mjs
```

## Rationale

1. **ES Modules**: We chose `.mjs` over `.js` to explicitly use ES modules, which is the modern JavaScript module system and aligns with Next.js's future direction.
2. **Centralized Configuration**: Having a single configuration file in the web app directory simplifies maintenance and avoids confusion.
3. **Comprehensive Optimization**: The standardized configuration includes optimizations for:
   - Image loading and optimization
   - Static file caching
   - CSS and JS compression
   - Progressive Web App (PWA) capabilities
   - Internationalization (i18n)

## Key Features

The standardized configuration includes:

### Performance Optimizations

- **Image Optimization**: Configured with appropriate formats, sizes, and caching
- **Compression**: Brotli and Gzip compression for static assets
- **CSS Optimization**: CSS splitting and optimization
- **Code Splitting**: Automatic code splitting for optimal loading

### Progressive Web App

- PWA support with service worker and offline caching
- Configurable caching strategies for different asset types
- Optimized for both performance and offline capabilities

### Internationalization

- Support for multiple languages (English, Spanish, French)
- Default locale configuration
- Automatic language detection

### Development Experience

- React Strict Mode for better development experience
- Bundle analyzer for performance monitoring
- Console removal in production builds

## Usage

To use this configuration:

1. Import the configuration in your Next.js application
2. No additional setup is required as the configuration is automatically applied

## Dependencies

The configuration relies on the following packages:

- `next-pwa`: For Progressive Web App support
- `@next/bundle-analyzer`: For bundle analysis
- `compression-webpack-plugin`: For Brotli and Gzip compression

These dependencies are listed in the `package.json` file of the web application.

## Removed Configurations

As part of this standardization, we have removed:

- `packages/config/frontend/next.config.js` (CommonJS version)
- `packages/config/frontend/next.config.mjs` (Duplicate configuration)

All projects should now reference the standardized configuration in `apps/web/next.config.mjs`.
