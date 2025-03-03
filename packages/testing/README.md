# Testing Utilities

This package provides shared testing utilities, fixtures, and helpers for use across all services in the Maily platform.

## Features

- **Test Fixtures**: Reusable test data and fixtures
- **Test Helpers**: Common helper functions for testing
- **Mocks**: Mock implementations of services and external dependencies
- **Test Setup**: Common setup and teardown utilities
- **Assertions**: Custom assertion utilities for testing domain logic

## Organization

- `fixtures/` - Reusable test data and fixtures
- `mocks/` - Mock implementations of services and external dependencies
- `helpers/` - Helper functions for testing
- `setup/` - Setup and teardown utilities
- `assertions/` - Custom assertion utilities

## Usage

### JavaScript/TypeScript

```typescript
import { createCampaignFixture } from '@maily/testing/fixtures/campaigns';
import { mockEmailService } from '@maily/testing/mocks/email-service';

describe('Campaign Service', () => {
  it('should send campaign emails', async () => {
    const campaign = createCampaignFixture();
    const mockEmail = mockEmailService();
    
    // Test implementation
  });
});
```

### Python

```python
from maily.testing.fixtures.campaigns import create_campaign_fixture
from maily.testing.mocks.email_service import mock_email_service

def test_campaign_sending():
    campaign = create_campaign_fixture()
    mock_email = mock_email_service()
    
    # Test implementation
```

## Adding New Test Utilities

When adding new test utilities:
1. Organize by domain or technical concept
2. Keep fixtures small and focused
3. Document usage with examples
4. Ensure compatibility with both JavaScript and Python tests where applicable