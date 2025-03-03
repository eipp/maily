# Configuration Schema

This package defines JSON schema validation for all configuration files used in the Maily platform. It ensures that configuration files are valid and complete before they are used in the application.

## Features

- JSON schema definitions for all configuration files
- Validation utilities for configuration files
- Type definitions for configuration objects
- Default configurations for development, testing, and production

## Organization

- `schemas/` - JSON schema definitions for configuration files
- `validators/` - Validation utilities for configuration files
- `defaults/` - Default configurations for different environments
- `types/` - TypeScript type definitions for configuration objects

## Usage

### JavaScript/TypeScript

```typescript
import { validateConfig } from '@maily/config-schema/validators';
import { AppConfig } from '@maily/config-schema/types';

const config: AppConfig = {
  // Configuration properties
};

const validationResult = validateConfig(config);
if (!validationResult.valid) {
  console.error('Invalid configuration:', validationResult.errors);
}
```

### Python

```python
from maily.config_schema.validators import validate_config

config = {
  # Configuration properties
}

validation_result = validate_config(config)
if not validation_result.valid:
  print(f'Invalid configuration: {validation_result.errors}')
```

## Adding New Schemas

When adding new configuration schemas:
1. Define the JSON schema in the `schemas/` directory
2. Add type definitions in the `types/` directory
3. Create default configurations in the `defaults/` directory
4. Update the validation utilities to support the new schema

## Benefits

Using a centralized configuration schema package:
- Prevents configuration errors
- Ensures consistent configuration across services
- Provides type safety for configuration objects
- Makes configuration changes more reliable