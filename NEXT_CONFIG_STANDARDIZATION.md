# Next.js Configuration Standardization

The following Next.js configuration files were consolidated:
- next.config.js (main configuration)
- next.config.mjs (ESM version)
- next.config.analyzer.js (with bundle analyzer)

Key considerations for the consolidated config:
1. Support for ESM modules
2. Bundle analyzer when needed (via environment variable)
3. Image optimization settings
4. Internationalization support
5. Environment variable handling
6. Security headers

To run with bundle analyzer:
```bash
ANALYZE=true npm run build:web
```
