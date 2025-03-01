# Maily Config Package

The config package provides centralized configuration management for all Maily services and applications.

## Features

- **Environment Variables**: Typed access to environment variables with validation
- **Configuration Schemas**: JSON schema validation for configuration objects
- **Default Values**: Sensible defaults for all configuration options
- **Configuration Merging**: Merge configurations from multiple sources
- **Secret Management**: Secure handling of sensitive configuration values
- **Context-aware Configs**: Different configurations for different environments

## Installation

```bash
pnpm add @maily/config
```

## Usage

```typescript
import { config, loadConfig } from '@maily/config';

// Access config values with type safety
const apiKey = config.api.key;
const databaseUrl = config.database.url;

// Load config from a specific source
const customConfig = await loadConfig('./custom-config.json');
```

## Configuration Schema

The configuration schema is defined in `src/schema.ts` and includes the following sections:

- **api**: API server configuration
- **database**: Database connection settings
- **email**: Email provider settings
- **auth**: Authentication settings
- **ai**: AI provider configurations
- **analytics**: Analytics settings
- **logging**: Logging configuration
- **monitoring**: Monitoring and alerting settings

## Environment Variables

The config package automatically loads environment variables from `.env` files based on the current environment:

- `.env.local`: Local development
- `.env.test`: Test environment
- `.env.production`: Production environment

## Secret Management

For secure handling of secrets, the config package supports:

- Environment variable substitution
- Vault integration
- AWS Secrets Manager
- Azure Key Vault

## Dependencies

- dotenv
- zod (for schema validation)
- deepmerge
