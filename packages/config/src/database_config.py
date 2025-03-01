"""
Database configuration for Maily.

Handles configuration for database connections, sharding, and read replicas.
"""
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

# Base database URLs
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")
READ_REPLICA_URL = os.environ.get("READ_REPLICA_URL", DATABASE_URL)  # Default to primary if no replica configured

# Sharding configuration
NUM_SHARDS = int(os.environ.get("NUM_SHARDS", "4"))
SHARDED_TABLES = ["emails", "tracking_events"]

# Shard database URLs (can be set via environment variables or use the defaults)
SHARD_URLS = {}
for i in range(NUM_SHARDS):
    env_var = f"SHARD_{i}_URL"
    default_url = f"postgresql://postgres:postgres@shard-{i}.maily:5432/maily_shard_{i}"
    SHARD_URLS[i] = os.environ.get(env_var, default_url)

# Archive database for historical data
ARCHIVE_DATABASE_URL = os.environ.get("ARCHIVE_DATABASE_URL",
                                     "postgresql://postgres:postgres@archive.maily:5432/maily_archive")

# Connection pool settings
MIN_POOL_SIZE = int(os.environ.get("DB_MIN_POOL_SIZE", "5"))
MAX_POOL_SIZE = int(os.environ.get("DB_MAX_POOL_SIZE", "20"))
POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "3600"))  # 1 hour
POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))

# Read/write split settings
READ_WRITE_SPLIT = os.environ.get("READ_WRITE_SPLIT", "true").lower() == "true"
ANALYTICS_QUERIES_TO_REPLICA = os.environ.get("ANALYTICS_QUERIES_TO_REPLICA", "true").lower() == "true"

# Archiving settings
ARCHIVE_THRESHOLD_DAYS = int(os.environ.get("ARCHIVE_THRESHOLD_DAYS", "90"))
ARCHIVE_BATCH_SIZE = int(os.environ.get("ARCHIVE_BATCH_SIZE", "1000"))

class QueryType(Enum):
    """Enum for different types of database queries."""
    READ = "read"
    WRITE = "write"
    ANALYTICS = "analytics"
    ARCHIVE = "archive"

class DatabaseType(Enum):
    """Enum for different types of databases."""
    PRIMARY = "primary"
    REPLICA = "replica"
    SHARD = "shard"
    ARCHIVE = "archive"

def get_connection_params(
    db_type: DatabaseType = DatabaseType.PRIMARY,
    shard_id: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Get database connection parameters.

    Args:
        db_type: Type of database to connect to
        shard_id: Shard ID (for sharded connections)
        **kwargs: Additional connection parameters

    Returns:
        Dictionary of connection parameters
    """
    params = {
        "pool_size": MIN_POOL_SIZE,
        "max_overflow": MAX_POOL_SIZE - MIN_POOL_SIZE,
        "pool_recycle": POOL_RECYCLE,
        "pool_timeout": POOL_TIMEOUT,
    }

    # Update with any additional parameters
    params.update(kwargs)

    return params

def get_db_url(
    query_type: QueryType = QueryType.READ,
    table_name: Optional[str] = None,
    shard_key: Optional[Any] = None
) -> str:
    """
    Get the appropriate database URL based on the query type and sharding.

    Args:
        query_type: Type of query (read, write, analytics, archive)
        table_name: Name of the table being queried
        shard_key: Key to use for sharding (user_id, campaign_id, etc.)

    Returns:
        Database URL to use
    """
    # For archive queries, use the archive database
    if query_type == QueryType.ARCHIVE:
        return ARCHIVE_DATABASE_URL

    # For analytics queries, use the read replica if configured
    if query_type == QueryType.ANALYTICS and ANALYTICS_QUERIES_TO_REPLICA and READ_REPLICA_URL != DATABASE_URL:
        return READ_REPLICA_URL

    # For read queries, use the read replica if split is enabled
    if query_type == QueryType.READ and READ_WRITE_SPLIT and READ_REPLICA_URL != DATABASE_URL:
        return READ_REPLICA_URL

    # For write queries, or if read/write split is disabled, use the primary
    if query_type == QueryType.WRITE or not READ_WRITE_SPLIT or READ_REPLICA_URL == DATABASE_URL:
        # Check if the table is sharded
        if table_name in SHARDED_TABLES and shard_key is not None:
            shard_id = calculate_shard_id(shard_key)
            return SHARD_URLS.get(shard_id, DATABASE_URL)

        return DATABASE_URL

def calculate_shard_id(shard_key: Any) -> int:
    """
    Calculate the shard ID for a given key.

    Args:
        shard_key: Key to use for sharding (user_id, campaign_id, etc.)

    Returns:
        Shard ID (0 to NUM_SHARDS-1)
    """
    # Convert key to string and hash it
    key_str = str(shard_key)
    hash_hex = hashlib.md5(key_str.encode()).hexdigest()

    # Convert first 8 hex chars to integer and mod by num_shards
    hash_int = int(hash_hex[:8], 16)
    shard_id = hash_int % NUM_SHARDS

    return shard_id

def should_archive_record(record_date: datetime) -> bool:
    """
    Determine if a record should be archived based on its age.

    Args:
        record_date: Date of the record

    Returns:
        True if the record should be archived, False otherwise
    """
    threshold_date = datetime.now() - timedelta(days=ARCHIVE_THRESHOLD_DAYS)
    return record_date < threshold_date

def get_engine_for_table(
    table_name: str,
    query_type: QueryType = QueryType.READ,
    shard_key: Optional[Any] = None
):
    """
    Get the appropriate SQLAlchemy engine for a table.

    Args:
        table_name: Name of the table
        query_type: Type of query
        shard_key: Key to use for sharding

    Returns:
        SQLAlchemy engine
    """
    from sqlalchemy import create_engine

    db_url = get_db_url(query_type, table_name, shard_key)
    db_type = (DatabaseType.SHARD if table_name in SHARDED_TABLES and shard_key is not None
              else DatabaseType.REPLICA if db_url == READ_REPLICA_URL
              else DatabaseType.ARCHIVE if db_url == ARCHIVE_DATABASE_URL
              else DatabaseType.PRIMARY)

    # Get connection parameters
    params = get_connection_params(db_type)

    # Create and return engine
    return create_engine(db_url, **params)

# Session management for sharded databases
def get_session_for_query(
    query_type: QueryType = QueryType.READ,
    table_name: Optional[str] = None,
    shard_key: Optional[Any] = None
):
    """
    Get the appropriate SQLAlchemy session for a query.

    Args:
        query_type: Type of query
        table_name: Name of the table
        shard_key: Key to use for sharding

    Returns:
        SQLAlchemy session
    """
    from sqlalchemy.orm import sessionmaker

    engine = get_engine_for_table(table_name, query_type, shard_key)
    Session = sessionmaker(bind=engine)
    return Session()

# Database migration helper
def get_all_db_urls() -> List[str]:
    """
    Get a list of all database URLs (for migrations).

    Returns:
        List of all database URLs
    """
    urls = [DATABASE_URL]

    # Add read replica if it's different
    if READ_REPLICA_URL != DATABASE_URL:
        urls.append(READ_REPLICA_URL)

    # Add shard URLs
    urls.extend(SHARD_URLS.values())

    # Add archive database
    urls.append(ARCHIVE_DATABASE_URL)

    # Remove duplicates
    return list(set(urls))
