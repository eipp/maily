"""
User service implementing standardized patterns and performance optimizations.
"""
from typing import Dict, Optional, List, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from models.user import User
from database.session import get_db
from errors.exceptions import NotFoundError, DatabaseError
from ..cache.tiered_cache_service import TieredCacheService, get_tiered_cache_service, CacheTier
from ..monitoring.performance_metrics import (
    PerformanceMetricsService,
    get_metrics_service,
    MetricType,
    DatabaseQueryTimer
)
from ..database.transaction import transactional

logger = structlog.get_logger("maily.services.user")


class UserService:
    """Service for managing user operations with optimized patterns."""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: Optional[TieredCacheService] = None,
        metrics_service: Optional[PerformanceMetricsService] = None
    ):
        """Initialize the user service.

        Args:
            db: SQLAlchemy database session
            cache_service: Tiered cache service
            metrics_service: Performance metrics service
        """
        self.db = db
        self.cache = cache_service or get_tiered_cache_service()
        self.metrics = metrics_service or get_metrics_service()

    async def get_user_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Get a user by Auth0 ID with caching.

        Args:
            auth0_id: The Auth0 ID of the user.

        Returns:
            The user if found, None otherwise.
        """
        # Define cache key
        cache_key = f"user:auth0:{auth0_id}"

        # Define getter function for cache miss
        async def db_getter():
            with DatabaseQueryTimer(self.metrics, "user_get_by_auth0_id", {"auth0_id": auth0_id}):
                try:
                    result = await self.db.execute(
                        select(User).where(User.auth0_id == auth0_id)
                    )
                    return result.scalars().first()
                except Exception as e:
                    logger.error(f"Error getting user by Auth0 ID: {str(e)}")
                    return None

        # Try to get from cache, or fetch from DB
        try:
            # Use get_or_set pattern with advanced caching
            user = await self.cache.get_or_set(
                key=cache_key,
                getter_func=db_getter,
                data_type="user_data",
                tier=CacheTier.NORMAL
            )

            self.metrics.record_metric(
                metric_type=MetricType.CACHE,
                name="user_get_by_auth0_id",
                duration_ms=0,
                metadata={"auth0_id": auth0_id, "cache_hit": True}
            )

            return user
        except Exception as e:
            # Log error and attempt direct DB access
            logger.error(
                "Cache error in get_user_by_auth0_id, falling back to database",
                auth0_id=auth0_id,
                error=str(e)
            )

            # Get directly from DB
            return await db_getter()

    async def get_user_by_id(self, user_id: str) -> User:
        """Get a user by ID with caching.

        Args:
            user_id: The ID of the user.

        Returns:
            The user.

        Raises:
            NotFoundError: If the user is not found.
        """
        # Define cache key
        cache_key = f"user:{user_id}"

        # Define getter function for cache miss
        async def db_getter():
            with DatabaseQueryTimer(self.metrics, "user_get_by_id", {"user_id": user_id}):
                try:
                    result = await self.db.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalars().first()
                    if not user:
                        raise NotFoundError(f"User with ID {user_id} not found")
                    return user
                except NotFoundError:
                    raise
                except Exception as e:
                    logger.error(f"Error getting user by ID: {str(e)}")
                    raise DatabaseError(f"Error retrieving user: {str(e)}")

        # Try to get from cache, or fetch from DB
        try:
            # Use get_or_set pattern with advanced caching
            user = await self.cache.get_or_set(
                key=cache_key,
                getter_func=db_getter,
                data_type="user_data",
                tier=CacheTier.NORMAL
            )

            self.metrics.record_metric(
                metric_type=MetricType.CACHE,
                name="user_get_by_id",
                duration_ms=0,
                metadata={"user_id": user_id, "cache_hit": True}
            )

            return user
        except NotFoundError:
            # Pass through not found errors
            raise
        except Exception as e:
            # Log error and attempt direct DB access
            logger.error(
                "Cache error in get_user_by_id, falling back to database",
                user_id=user_id,
                error=str(e)
            )

            # Get directly from DB
            return await db_getter()

    @transactional
    async def create_user_from_auth0(self, auth0_data: Dict[str, Any]) -> User:
        """Create a new user from Auth0 data with performance monitoring.

        Args:
            auth0_data: The Auth0 user data.

        Returns:
            The created user.
        """
        # Use metrics decorator
        with DatabaseQueryTimer(self.metrics, "user_create_from_auth0", {"source": "service"}):
            try:
                # Extract user data from Auth0 payload
                auth0_id = auth0_data.get("sub")
                email = auth0_data.get("email")
                name = auth0_data.get("name")
                picture = auth0_data.get("picture")

                # Default roles
                roles = ["user"]

                # Create new user
                user = User(
                    auth0_id=auth0_id,
                    email=email,
                    name=name,
                    picture=picture,
                    roles=roles
                )

                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)

                # Invalidate any cache entries
                await self._invalidate_user_cache(user)

                logger.info(f"Created new user from Auth0: {user.id}")
                return user
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Error creating user from Auth0: {str(e)}")
                raise DatabaseError(f"Error creating user: {str(e)}")

    @transactional
    async def update_user(self, user_id: str, data: Dict[str, Any]) -> User:
        """Update a user with performance monitoring.

        Args:
            user_id: The ID of the user to update.
            data: The data to update.

        Returns:
            The updated user.
        """
        with DatabaseQueryTimer(self.metrics, "user_update", {"user_id": user_id}):
            try:
                # Get the user first
                user = await self.get_user_by_id(user_id)

                # Update user fields
                for key, value in data.items():
                    if hasattr(user, key) and key != "id" and key != "auth0_id":
                        setattr(user, key, value)

                await self.db.commit()
                await self.db.refresh(user)

                # Invalidate any cache entries
                await self._invalidate_user_cache(user)

                return user
            except NotFoundError:
                raise
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Error updating user: {str(e)}")
                raise DatabaseError(f"Error updating user: {str(e)}")

    async def _invalidate_user_cache(self, user: User) -> None:
        """Invalidate cache entries for a user.

        Args:
            user: The user object
        """
        try:
            if user.id:
                await self.cache.delete(f"user:{user.id}")
            if user.email:
                await self.cache.delete(f"user:email:{user.email}")
            if hasattr(user, 'auth0_id') and user.auth0_id:
                await self.cache.delete(f"user:auth0:{user.auth0_id}")
        except Exception as e:
            logger.error(f"Error invalidating user cache: {str(e)}")


# Create singleton instance
_user_service = None

async def get_user_service(db: Optional[AsyncSession] = None) -> UserService:
    """Get or create a UserService instance.

    Args:
        db: Optional database session.

    Returns:
        UserService instance.
    """
    global _user_service

    if _user_service is None or db is not None:
        if db is None:
            db = await anext(get_db())
        _user_service = UserService(db)

    return _user_service


# Legacy/Compatibility Functions

async def get_user_by_auth0_id(auth0_id: str, db: Optional[AsyncSession] = None) -> Optional[User]:
    """Get a user by Auth0 ID (legacy function).

    Args:
        auth0_id: The Auth0 ID of the user.
        db: Optional database session.

    Returns:
        The user if found, None otherwise.
    """
    service = await get_user_service(db)
    return await service.get_user_by_auth0_id(auth0_id)


async def get_user_by_id(user_id: str, db: Optional[AsyncSession] = None) -> User:
    """Get a user by ID (legacy function).

    Args:
        user_id: The ID of the user.
        db: Optional database session.

    Returns:
        The user.

    Raises:
        NotFoundError: If the user is not found.
    """
    service = await get_user_service(db)
    return await service.get_user_by_id(user_id)


async def create_user_from_auth0(auth0_data: Dict[str, Any], db: Optional[AsyncSession] = None) -> User:
    """Create a new user from Auth0 data (legacy function).

    Args:
        auth0_data: The Auth0 user data.
        db: Optional database session.

    Returns:
        The created user.
    """
    service = await get_user_service(db)
    return await service.create_user_from_auth0(auth0_data)


async def update_user(user_id: str, data: Dict[str, Any], db: Optional[AsyncSession] = None) -> User:
    """Update a user (legacy function).

    Args:
        user_id: The ID of the user to update.
        data: The data to update.
        db: Optional database session.

    Returns:
        The updated user.
    """
    service = await get_user_service(db)
    return await service.update_user(user_id, data)
