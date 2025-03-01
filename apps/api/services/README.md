# Maily API Services

This directory contains service modules that implement the business logic for the Maily API.

## Service Organization

Services are organized by domain and follow a clean architecture approach:

```
services/
├── auth/                  # Authentication and authorization services
├── campaign/              # Campaign management services
├── contact/               # Contact management services
├── email/                 # Email sending and tracking services
├── template/              # Email template services
├── analytics/             # Analytics and reporting services
├── integration/           # Third-party integration services
├── ai/                    # AI-related services
└── common/                # Shared service utilities
```

## Service Responsibilities

Services are responsible for:

1. Implementing business logic
2. Orchestrating data access through repositories
3. Enforcing business rules and validations
4. Handling complex operations that span multiple domains
5. Providing a clean API for routers to consume

## Service Structure

Each service module should:

1. Define a class with methods for specific operations
2. Accept dependencies through constructor injection
3. Be stateless when possible
4. Include proper type annotations
5. Handle errors appropriately

Example:

```python
from typing import List, Optional
from datetime import datetime

from apps.api.models.campaign import Campaign
from apps.api.repositories.campaign import CampaignRepository
from apps.api.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignService:
    def __init__(self, repository: CampaignRepository):
        self.repository = repository

    async def get_campaigns(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Campaign]:
        """
        Get all campaigns for a user.
        """
        return await self.repository.get_by_user(user_id, limit, offset)

    async def get_campaign(self, campaign_id: int, user_id: int) -> Optional[Campaign]:
        """
        Get a campaign by ID for a specific user.
        """
        campaign = await self.repository.get_by_id(campaign_id)
        if campaign and campaign.user_id == user_id:
            return campaign
        return None

    async def create_campaign(self, user_id: int, data: CampaignCreate) -> Campaign:
        """
        Create a new campaign for a user.
        """
        # Business logic and validation here
        campaign_data = data.dict()
        campaign_data["user_id"] = user_id
        campaign_data["created_at"] = datetime.utcnow()

        return await self.repository.create(campaign_data)
```

## Dependency Injection

Services should follow dependency injection principles:

1. Dependencies should be passed through the constructor
2. Services should not directly instantiate dependencies
3. Dependencies should be defined as interfaces/protocols when possible

## Error Handling

Services should:

1. Raise specific exceptions for business rule violations
2. Handle expected errors gracefully
3. Let unexpected errors propagate to the global error handler
4. Include context in error messages

## Testing

All services should have tests that:

1. Test the business logic in isolation
2. Mock dependencies
3. Cover success and error cases
4. Test edge cases

## Best Practices

1. **Single Responsibility**: Each service should focus on a single domain.
2. **Thin Services**: Keep services focused on business logic, not data access.
3. **Stateless**: Services should be stateless when possible.
4. **Validation**: Validate inputs before processing.
5. **Documentation**: Include docstrings for all service methods.
6. **Logging**: Log important operations and errors.
