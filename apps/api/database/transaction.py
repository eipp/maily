"""
Transaction management for database operations.
"""
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import structlog
from typing import Generator, Optional, Callable, Any

logger = structlog.get_logger("justmaily.database")

@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """Context manager for database transactions.

    Provides automatic commit/rollback handling for database operations.
    In case of an exception, the transaction will be rolled back.

    Args:
        db: SQLAlchemy database session

    Yields:
        The database session

    Example:
        ```python
        with transaction(db_session) as session:
            user = User(name="John Doe")
            session.add(user)
            # Will be automatically committed if no exception occurs
            # or rolled back if an exception is raised
        ```
    """
    try:
        # Yield the session to the caller
        yield db
        # If we get here, no exception was raised, so commit the transaction
        db.commit()
    except SQLAlchemyError as e:
        # Rollback on SQLAlchemy errors
        db.rollback()
        # Log the error with context
        logger.error(
            "Database transaction error",
            exc_info=True,
            error_type=e.__class__.__name__,
            error_message=str(e)
        )
        # Re-raise the exception
        raise
    except Exception as e:
        # Also rollback on other exceptions
        db.rollback()
        # Log the error with context
        logger.error(
            "Transaction error (non-database)",
            exc_info=True,
            error_type=e.__class__.__name__,
            error_message=str(e)
        )
        # Re-raise the exception
        raise

def transactional(func: Callable) -> Callable:
    """Decorator for functions that need transaction management.

    Args:
        func: The function to decorate

    Returns:
        The decorated function

    Example:
        ```python
        @transactional
        def create_user(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            return user
        ```
    """
    def wrapper(*args, **kwargs):
        # Find the database session in args or kwargs
        db = None
        for arg in args:
            if isinstance(arg, Session):
                db = arg
                break

        if db is None:
            db = kwargs.get('db')

        if db is None:
            raise ValueError("No database session provided to transactional function")

        # Use the transaction context manager
        with transaction(db):
            return func(*args, **kwargs)

    # Update wrapper metadata to match the original function
    from functools import update_wrapper
    update_wrapper(wrapper, func)
    return wrapper
