# @maily/models

Shared data models for the Maily platform.

## Overview

This package contains shared data models used across different services in the Maily platform. By centralizing model definitions, we ensure consistency and reduce duplication.

## Structure

The package is organized into two main directories:

- `typescript/`: TypeScript interfaces and type definitions
- `python/`: Python models and schemas

## Usage

### TypeScript

```typescript
import { Campaign, Recommendation } from '@maily/models';

// Use the shared model
const campaign: Campaign = {
  id: '123',
  name: 'Q1 Newsletter',
  // ...other fields
};
```

### Python

```python
from maily_models import Campaign, Recommendation

# Use the shared model
campaign = Campaign(
    id="123",
    name="Q1 Newsletter",
    # ...other fields
)
```

## Available Models

- Campaign
- Contact
- User
- Template
- Recommendation
- Analytics
- Metrics

## Development

When adding or modifying models, make sure to:

1. Update both TypeScript and Python definitions
2. Add validation when applicable
3. Write tests for new models
4. Update this README if you add new model categories