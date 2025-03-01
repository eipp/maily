"""
Database session utilities for Maily.

This module provides utilities for managing database sessions,
including sharded databases and read replicas.
"""
import logging
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator, Union, Type, List

from sqlalchemy import create_engine, inspect, Table, Column
from sqlalchemy.orm import sessionmaker, Session, declarative_base, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Selectable

from backend.config.database_config import (
    DATABASE_URL, READ_REPLICA_URL, SHARD_URLS, ARCHIVE_DATABASE_URL,
    QueryType, DatabaseType, get_connection_params, calculate_shard_id,
    get_db_url, get_engine_for_table, SHARDED_TABLES
)

logger = logging.getLogger(__name__)

# Thread-local storage for database connections
thread_local = threading.local()

# Base class for SQLAlchemy models
Base = declarative_base()

# Engine cache to avoid creating multiple engines for the same URL
engine_cache: Dict[str, Engine] = {}

# Session factories cache
session_factory_cache: Dict[str, sessionmaker] = {}

def get_engine(url: str, **kwargs) -> Engine:
    """
    Get a SQLAlchemy engine for a database URL.

    Args:
        url: Database URL
        **kwargs: Additional connection parameters

    Returns:
        SQLAlchemy engine
    """
    if url not in engine_cache:
        logger.debug(f"Creating new engine for URL: {url}")
        engine_cache[url] = create_engine(url, **kwargs)
    return engine_cache[url]

def get_session_factory(url: str, **kwargs) -> sessionmaker:
    """
    Get a session factory for a database URL.

    Args:
        url: Database URL
        **kwargs: Additional connection parameters

    Returns:
        SQLAlchemy sessionmaker
    """
    if url not in session_factory_cache:
        engine = get_engine(url, **kwargs)
        session_factory_cache[url] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory_cache[url]

def get_primary_session() -> Session:
    """
    Get a session for the primary database.

    Returns:
        SQLAlchemy session
    """
    params = get_connection_params(DatabaseType.PRIMARY)
    factory = get_session_factory(DATABASE_URL, **params)
    return factory()

def get_replica_session() -> Session:
    """
    Get a session for the read replica database.

    Returns:
        SQLAlchemy session
    """
    params = get_connection_params(DatabaseType.REPLICA)
    factory = get_session_factory(READ_REPLICA_URL, **params)
    return factory()

def get_archive_session() -> Session:
    """
    Get a session for the archive database.

    Returns:
        SQLAlchemy session
    """
    params = get_connection_params(DatabaseType.ARCHIVE)
    factory = get_session_factory(ARCHIVE_DATABASE_URL, **params)
    return factory()

def get_shard_session(shard_id: int) -> Session:
    """
    Get a session for a specific shard.

    Args:
        shard_id: Shard ID

    Returns:
        SQLAlchemy session
    """
    if shard_id not in SHARD_URLS:
        raise ValueError(f"Invalid shard ID: {shard_id}")

    params = get_connection_params(DatabaseType.SHARD, shard_id=shard_id)
    factory = get_session_factory(SHARD_URLS[shard_id], **params)
    return factory()

def get_session_for_table(
    table_name: str,
    query_type: QueryType = QueryType.READ,
    shard_key: Optional[Any] = None
) -> Session:
    """
    Get the appropriate session for a table based on query type and sharding.

    Args:
        table_name: Name of the table
        query_type: Type of query
        shard_key: Key to use for sharding

    Returns:
        SQLAlchemy session
    """
    db_url = get_db_url(query_type, table_name, shard_key)

    # Determine the database type
    db_type = DatabaseType.PRIMARY
    if db_url == READ_REPLICA_URL:
        db_type = DatabaseType.REPLICA
    elif db_url == ARCHIVE_DATABASE_URL:
        db_type = DatabaseType.ARCHIVE
    elif table_name in SHARDED_TABLES and shard_key is not None:
        db_type = DatabaseType.SHARD

    # Get connection parameters
    params = get_connection_params(db_type,
                                  shard_id=calculate_shard_id(shard_key) if shard_key is not None else None)

    # Get session factory and create session
    factory = get_session_factory(db_url, **params)
    return factory()

@contextmanager
def session_scope(
    query_type: QueryType = QueryType.READ,
    table_name: Optional[str] = None,
    shard_key: Optional[Any] = None
) -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Args:
        query_type: Type of query
        table_name: Name of the table
        shard_key: Key to use for sharding

    Yields:
        SQLAlchemy session
    """
    session = get_session_for_table(table_name, query_type, shard_key) if table_name else get_primary_session()
    try:
        yield session
        if query_type == QueryType.WRITE:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class ShardedSession:
    """
    Session manager for sharded tables.

    This class provides methods for querying and manipulating sharded tables.
    """

    def __init__(self):
        """Initialize the sharded session."""
        self.primary_session = get_primary_session()
        self.sessions: Dict[int, Session] = {}

    def get_session_for_shard(self, shard_id: int) -> Session:
        """
        Get a session for a specific shard.

        Args:
            shard_id: Shard ID

        Returns:
            SQLAlchemy session
        """
        if shard_id not in self.sessions:
            self.sessions[shard_id] = get_shard_session(shard_id)
        return self.sessions[shard_id]

    def query_by_shard_key(
        self,
        model_class: Type[Base],
        shard_key: Any,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Query a sharded table using a shard key.

        Args:
            model_class: SQLAlchemy model class
            shard_key: Key to use for sharding
            *args: Additional positional arguments for the query
            **kwargs: Additional keyword arguments for the query

        Returns:
            Query result
        """
        # Check if the model is for a sharded table
        table_name = model_class.__tablename__
        if table_name not in SHARDED_TABLES:
            return self.primary_session.query(model_class, *args).filter_by(**kwargs)

        # Calculate shard ID
        shard_id = calculate_shard_id(shard_key)

        # Get session for the shard
        session = self.get_session_for_shard(shard_id)

        # Execute query on the shard
        return session.query(model_class, *args).filter_by(**kwargs)

    def query_all_shards(
        self,
        model_class: Type[Base],
        *args: Any,
        **kwargs: Any
    ) -> List[Any]:
        """
        Query across all shards and combine the results.

        Args:
            model_class: SQLAlchemy model class
            *args: Additional positional arguments for the query
            **kwargs: Additional keyword arguments for the query

        Returns:
            Combined query results from all shards
        """
        # Check if the model is for a sharded table
        table_name = model_class.__tablename__
        if table_name not in SHARDED_TABLES:
            return list(self.primary_session.query(model_class, *args).filter_by(**kwargs))

        # Query each shard and combine results
        results = []
        for shard_id in SHARD_URLS.keys():
            session = self.get_session_for_shard(shard_id)
            shard_results = session.query(model_class, *args).filter_by(**kwargs).all()
            results.extend(shard_results)

        return results

    def add(self, obj: Base) -> None:
        """
        Add an object to the appropriate database.

        Args:
            obj: SQLAlchemy model instance
        """
        # Check if the object is for a sharded table
        table_name = obj.__tablename__
        if table_name not in SHARDED_TABLES:
            self.primary_session.add(obj)
            return

        # Determine the shard key and ID
        shard_key = getattr(obj, "campaign_id", None) or getattr(obj, "user_id", None)
        if shard_key is None:
            raise ValueError(f"No shard key found for object: {obj}")

        shard_id = calculate_shard_id(shard_key)

        # Add to the appropriate shard
        session = self.get_session_for_shard(shard_id)
        session.add(obj)

    def delete(self, obj: Base) -> None:
        """
        Delete an object from the appropriate database.

        Args:
            obj: SQLAlchemy model instance
        """
        # Check if the object is for a sharded table
        table_name = obj.__tablename__
        if table_name not in SHARDED_TABLES:
            self.primary_session.delete(obj)
            return

        # Determine the shard key and ID
        shard_key = getattr(obj, "campaign_id", None) or getattr(obj, "user_id", None)
        if shard_key is None:
            raise ValueError(f"No shard key found for object: {obj}")

        shard_id = calculate_shard_id(shard_key)

        # Delete from the appropriate shard
        session = self.get_session_for_shard(shard_id)
        session.delete(obj)

    def commit(self) -> None:
        """Commit changes to all active sessions."""
        # Commit primary session
        self.primary_session.commit()

        # Commit all shard sessions
        for session in self.sessions.values():
            session.commit()

    def rollback(self) -> None:
        """Rollback changes from all active sessions."""
        # Rollback primary session
        self.primary_session.rollback()

        # Rollback all shard sessions
        for session in self.sessions.values():
            session.rollback()

    def close(self) -> None:
        """Close all active sessions."""
        # Close primary session
        self.primary_session.close()

        # Close all shard sessions
        for session in self.sessions.values():
            session.close()

    def __enter__(self) -> 'ShardedSession':
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

@contextmanager
def sharded_session_scope() -> Generator[ShardedSession, None, None]:
    """
    Context manager for sharded sessions.

    Yields:
        ShardedSession instance
    """
    session = ShardedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_sharded_tables() -> None:
    """
    Initialize sharded tables in all shards.

    This function ensures that all sharded tables exist in all shards.
    """
    # Create metadata for the base
    metadata = Base.metadata

    # Get the primary engine
    primary_engine = get_engine(DATABASE_URL)

    # Create tables in the primary database
    metadata.create_all(primary_engine)

    # Create sharded tables in each shard
    for shard_id, shard_url in SHARD_URLS.items():
        shard_engine = get_engine(shard_url)

        # Create only the sharded tables in the shard
        tables_to_create = []
        for table_name, table in metadata.tables.items():
            if table_name in SHARDED_TABLES:
                tables_to_create.append(table)

        if tables_to_create:
            # Create metadata with only the sharded tables
            metadata.create_all(shard_engine, tables=tables_to_create)
            logger.info(f"Created sharded tables in shard {shard_id}")

# Examples of how to use these utilities:
#
# 1. Simple query using the appropriate session type:
# with session_scope(QueryType.READ) as session:
#     users = session.query(User).filter_by(active=True).all()
#
# 2. Query to a sharded table:
# with session_scope(QueryType.READ, "emails", campaign_id=123) as session:
#     emails = session.query(Email).filter_by(campaign_id=123).all()
#
# 3. Writing to a sharded table:
# with session_scope(QueryType.WRITE, "emails", campaign_id=123) as session:
#     email = Email(campaign_id=123, recipient_id=456, subject="Test")
#     session.add(email)
#     # Commit is automatic at the end of the with block
#
# 4. Using the ShardedSession for more control:
# with sharded_session_scope() as session:
#     # Query a specific shard
#     emails = session.query_by_shard_key(Email, 123).all()
#
#     # Query across all shards
#     all_emails = session.query_all_shards(Email, campaign_id=123)
#
#     # Add a new object to the appropriate shard
#     email = Email(campaign_id=123, recipient_id=456, subject="Test")
#     session.add(email)
#
#     # Commit is automatic at the end of the with block
