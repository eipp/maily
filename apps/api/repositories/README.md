# Maily API Repositories

This directory contains repository modules that handle data access for the Maily API.

## Repository Pattern

The repository pattern is used to:

1. Abstract database operations from business logic
2. Provide a consistent interface for data access
3. Simplify testing by allowing repository mocking
4. Centralize data access logic

## Repository Organization

Repositories are organized by domain entity:

```
repositories/
├── auth/                  # Authentication-related repositories
├── campaign/              # Campaign repositories
├── contact/               # Contact repositories
├── email/                 # Email repositories
├── template/              # Template repositories
├── analytics/             # Analytics repositories
├── integration/           # Integration repositories
└── base.py                # Base repository class
```

## Repository Responsibilities

Repositories are responsible for:

1. CRUD operations on database entities
2. Query construction and execution
3. Data mapping between database and domain models
4. Transaction management
5. Optimizing database access

## Repository Structure

Each repository should:

1. Extend the base repository class
2. Define methods for specific data access operations
3. Use SQLAlchemy for database operations
4. Include proper type annotations
5. Handle database errors appropriately

Example:

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from apps.api.models.campaign import Campaign
from apps.api.repositories.base import BaseRepository


class CampaignRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Campaign)

    async def get_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Campaign]:
        """
        Get all campaigns for a user.
        """
        query = select(Campaign).where(Campaign.user_id == user_id).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, campaign_id: int) -> Optional[Campaign]:
        """
        Get a campaign by ID.
        """
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, data: Dict[str, Any]) -> Campaign:
        """
        Create a new campaign.
        """
        campaign = Campaign(**data)
        self.session.add(campaign)
        await self.session.commit()
        await self.session.refresh(campaign)
        return campaign

    async def update(self, campaign_id: int, data: Dict[str, Any]) -> Optional[Campaign]:
        """
        Update a campaign.
        """
        query = update(Campaign).where(Campaign.id == campaign_id).values(**data).returning(Campaign)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalars().first()

    async def delete(self, campaign_id: int) -> bool:
        """
        Delete a campaign.
        """
        query = delete(Campaign).where(Campaign.id == campaign_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
```

## Base Repository

The base repository (`base.py`) provides common CRUD operations that can be inherited by specific repositories:

```python
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from apps.api.db.base import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        query = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, id: int) -> Optional[T]:
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, data: Dict[str, Any]) -> T:
        obj = self.model_class(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        query = update(self.model_class).where(self.model_class.id == id).values(**data).returning(self.model_class)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalars().first()

    async def delete(self, id: int) -> bool:
        query = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
```

## Dependency Injection

Repositories should be injected into services:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db.session import get_db
from apps.api.repositories.campaign import CampaignRepository


def get_campaign_repository(session: AsyncSession = Depends(get_db)) -> CampaignRepository:
    return CampaignRepository(session)
```

## Testing

All repositories should have tests that:

1. Use an in-memory SQLite database or test PostgreSQL instance
2. Test all CRUD operations
3. Test specific query methods
4. Test error cases

## Best Practices

1. **Single Responsibility**: Each repository should focus on a single entity.
2. **Thin Repositories**: Keep repositories focused on data access, not business logic.
3. **Query Optimization**: Use efficient queries and avoid N+1 problems.
4. **Transactions**: Use transactions for operations that modify multiple entities.
5. **Error Handling**: Handle database errors gracefully.
6. **Documentation**: Include docstrings for all repository methods.
