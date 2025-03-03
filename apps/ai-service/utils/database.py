"""
Database utility module for the AI Service.

This module provides database connection and session management for the AI Service,
with support for SQLAlchemy ORM, connection pooling, and database migrations.
"""

import os
import time
import logging
from typing import Any, Dict, Generator, Optional, Union
from contextlib import contextmanager

from sqlalchemy import create_engine, event, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    echo=ECHO_SQL,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Add event listeners for connection pool
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.debug("Database connection established")
    connection_record.info["pid"] = os.getpid()

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        logger.debug(f"Connection record PID ({connection_record.info['pid']}) does not match current PID ({pid}), resetting")
        connection_record.connection = None
        connection_record.info["pid"] = pid
        raise exc.DisconnectionError("Connection record belongs to a different process")

@event.listens_for(engine, "checkin")
def checkin(dbapi_connection, connection_record):
    logger.debug("Database connection returned to pool")

# Context manager for database sessions
@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a database session with automatic commit/rollback and connection handling.
    
    This function provides a context manager that yields a SQLAlchemy session,
    automatically handling commits on successful execution and rollbacks on exceptions.
    It also ensures proper connection cleanup and returns connections to the pool.
    
    Example:
        ```python
        with get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            user.name = "New Name"
            # No need to call session.commit() - it's handled automatically
        ```
    
    Yields:
        Session: A SQLAlchemy session object
    
    Raises:
        Exception: Any exception that occurs during the session is re-raised after rollback
    """
    session = SessionLocal()
    try:
        # Start a new transaction
        logger.debug("Starting new database transaction")
        
        # Yield the session to the caller
        yield session
        
        # Commit the transaction if no exception occurred
        session.commit()
        logger.debug("Database transaction committed")
    except Exception as e:
        # Rollback the transaction on exception
        session.rollback()
        logger.error(f"Database transaction rolled back due to error: {str(e)}")
        raise
    finally:
        # Close the session in all cases
        session.close()
        logger.debug("Database session closed")

def check_database_connection() -> Dict[str, Any]:
    """
    Check database connection and return status information.
    
    This function attempts to connect to the database and execute a simple query
    to verify that the connection is working properly. It returns a dictionary
    with status information, including connection success/failure, response time,
    and pool statistics.
    
    Returns:
        Dict[str, Any]: Dictionary with connection status information
    """
    start_time = time.time()
    status = {
        "success": False,
        "message": "",
        "response_time_ms": 0,
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
        "current_connections": 0,
    }
    
    try:
        # Get connection from pool
        with engine.connect() as connection:
            # Execute simple query
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            
            # Get pool statistics
            status["current_connections"] = engine.pool.checkedout()
            
            # Update status
            status["success"] = True
            status["message"] = "Database connection successful"
    except Exception as e:
        status["success"] = False
        status["message"] = f"Database connection failed: {str(e)}"
    finally:
        # Calculate response time
        end_time = time.time()
        status["response_time_ms"] = round((end_time - start_time) * 1000, 2)
    
    return status

def execute_migration(migration_sql: str) -> bool:
    """
    Execute a database migration script.
    
    This function executes a SQL migration script within a transaction,
    rolling back if any errors occur.
    
    Args:
        migration_sql (str): SQL migration script to execute
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        with engine.begin() as connection:
            connection.execute(text(migration_sql))
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

def get_table_names() -> list:
    """
    Get a list of all tables in the database.
    
    Returns:
        list: List of table names
    """
    inspector = inspect(engine)
    return inspector.get_table_names()

# Initialize database connection
def init_db():
    """
    Initialize the database connection and create tables.
    
    This function should be called during application startup to ensure
    that the database connection is properly initialized and all tables
    defined in the models are created if they don't exist.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

# Import models at the bottom to avoid circular imports
from sqlalchemy import inspect
from ai_service.models.ai_session import AISession
from ai_service.models.ai_model import AIModel
from ai_service.models.ai_prompt import AIPrompt
