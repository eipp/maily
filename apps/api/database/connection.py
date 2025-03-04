"""
Database connection management with enhanced connection pooling.

This module provides utilities for managing database connections with:
- Connection pooling with configurable settings
- Automatic retries with exponential backoff
- Connection health monitoring
- Read/write splitting
- Database metrics collection
"""

import os
import time
import logging
import random
from typing import Dict, Any, Optional, List, Tuple, Callable, TypeVar, Union
from functools import wraps
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool, PoolError
from psycopg2.extras import DictCursor, RealDictCursor, Json
from psycopg2 import sql, DatabaseError, OperationalError
from prometheus_client import Counter, Histogram, Gauge
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
DB_OPERATION_LATENCY = Histogram(
    'db_operation_latency_seconds',
    'Database operation latency in seconds',
    ['operation', 'pool']
)
DB_OPERATION_TOTAL = Counter(
    'db_operation_total',
    'Total number of database operations',
    ['operation', 'pool', 'status']
)
DB_POOL_SIZE = Gauge(
    'db_pool_size',
    'Current database pool size',
    ['pool']
)
DB_POOL_USAGE = Gauge(
    'db_pool_usage',
    'Current database pool usage',
    ['pool']
)

# Connection pool settings
DEFAULT_MIN_CONN = int(os.environ.get("DB_MIN_CONNECTIONS", "5"))
DEFAULT_MAX_CONN = int(os.environ.get("DB_MAX_CONNECTIONS", "20"))
DEFAULT_RETRY_COUNT = int(os.environ.get("DB_RETRY_COUNT", "3"))
DEFAULT_RETRY_DELAY = float(os.environ.get("DB_RETRY_DELAY", "0.5"))
DEFAULT_MAX_RETRY_DELAY = float(os.environ.get("DB_MAX_RETRY_DELAY", "10.0"))

# Type variable
T = TypeVar('T')

class DatabaseConnectionManager:
    """
    Manages database connections with connection pooling, retries, and monitoring.

    Features:
    - Connection pooling with configurable settings
    - Automatic retries with exponential backoff
    - Connection health monitoring
    - Support for read/write operations
    - Prometheus metrics
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the database connection manager."""
        if self._initialized:
            return

        self._initialized = True
        self.pools = {}
        self.retry_strategy = tenacity.retry(
            retry=retry_if_exception_type((OperationalError, PoolError)),
            stop=stop_after_attempt(DEFAULT_RETRY_COUNT),
            wait=wait_exponential(multiplier=DEFAULT_RETRY_DELAY, max=DEFAULT_MAX_RETRY_DELAY),
            before_sleep=lambda retry_state: logger.warning(
                f"Retrying database operation after error: {retry_state.outcome.exception()}"
            ),
        )

        # Initialize the default pool
        self._initialize_default_pool()

    def _initialize_default_pool(self):
        """Initialize the default connection pool."""
        # Get database connection parameters from environment
        db_params = {
            "dbname": os.environ.get("POSTGRES_DB", "maily"),
            "user": os.environ.get("POSTGRES_USER", "postgres"),
            "password": os.environ.get("POSTGRES_PASSWORD", ""),
            "host": os.environ.get("POSTGRES_HOST", "localhost"),
            "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        }
        
        # Check if DATABASE_URL is provided (preferred connection method)
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            logger.info("Using DATABASE_URL for connection parameters")
            db_params = {"dsn": database_url}

        # Create the default pool
        self.create_pool("default", db_params, DEFAULT_MIN_CONN, DEFAULT_MAX_CONN)

        # Create read replica pool if read replica is configured
        read_host = os.environ.get("POSTGRES_READ_HOST")
        if read_host:
            read_params = db_params.copy()
            read_params["host"] = read_host
            read_params["port"] = int(os.environ.get("POSTGRES_READ_PORT", "5432"))
            self.create_pool("read_replica", read_params, DEFAULT_MIN_CONN, DEFAULT_MAX_CONN)

    def create_pool(self, name: str, db_params: Dict[str, Any], min_conn: int, max_conn: int):
        """Create a new connection pool."""
        try:
            logger.info(f"Creating connection pool '{name}' with min={min_conn}, max={max_conn}")
            pool = ThreadedConnectionPool(minconn=min_conn, maxconn=max_conn, **db_params)
            self.pools[name] = {
                "pool": pool,
                "params": db_params,
                "min_conn": min_conn,
                "max_conn": max_conn,
                "used_connections": 0,
            }
            DB_POOL_SIZE.labels(pool=name).set(max_conn)
            DB_POOL_USAGE.labels(pool=name).set(0)
            logger.info(f"Connection pool '{name}' created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create connection pool '{name}': {e}")
            return False

    def close_pools(self):
        """Close all connection pools."""
        for name, pool_info in self.pools.items():
            logger.info(f"Closing connection pool '{name}'")
            try:
                pool_info["pool"].closeall()
                logger.info(f"Connection pool '{name}' closed successfully")
            except Exception as e:
                logger.error(f"Error closing connection pool '{name}': {e}")

    @contextmanager
    def get_connection(self, pool_name: str = "default", for_write: bool = False):
        """
        Get a connection from the specified pool.

        Args:
            pool_name: Name of the pool to get connection from
            for_write: Whether this connection is for write operations

        Yields:
            A database connection
        """
        # If this is a read operation and we have a read replica, use it
        if not for_write and "read_replica" in self.pools and pool_name == "default":
            pool_name = "read_replica"

        if pool_name not in self.pools:
            logger.warning(f"Pool '{pool_name}' not found, using default pool")
            pool_name = "default"

        pool_info = self.pools[pool_name]
        conn = None
        start_time = time.time()
        operation = "write" if for_write else "read"

        try:
            # Get connection from pool with retry
            conn = self.retry_strategy(pool_info["pool"].getconn)
            pool_info["used_connections"] += 1
            DB_POOL_USAGE.labels(pool=pool_name).set(pool_info["used_connections"])

            # Set application name for easier identification in database logs
            cursor = conn.cursor()
            cursor.execute(f"SET application_name TO 'maily_{operation}'")
            cursor.close()

            # Yield the connection
            yield conn

            # Record success
            DB_OPERATION_TOTAL.labels(operation=operation, pool=pool_name, status="success").inc()

        except Exception as e:
            # Record failure
            DB_OPERATION_TOTAL.labels(operation=operation, pool=pool_name, status="error").inc()
            logger.error(f"Database error from pool '{pool_name}': {e}")

            # Rollback transaction if needed
            if conn is not None:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error rolling back transaction: {rollback_error}")

            # Reraise the exception
            raise

        finally:
            # Return connection to the pool
            if conn is not None:
                try:
                    pool_info["pool"].putconn(conn)
                    pool_info["used_connections"] -= 1
                    DB_POOL_USAGE.labels(pool=pool_name).set(pool_info["used_connections"])
                except Exception as e:
                    logger.error(f"Error returning connection to pool '{pool_name}': {e}")

            # Record operation latency
            latency = time.time() - start_time
            DB_OPERATION_LATENCY.labels(operation=operation, pool=pool_name).observe(latency)

    @contextmanager
    def get_cursor(self, cursor_factory=DictCursor, pool_name: str = "default", for_write: bool = False):
        """
        Get a database cursor from the specified pool.

        Args:
            cursor_factory: Cursor factory to use
            pool_name: Name of the pool to get cursor from
            for_write: Whether this cursor is for write operations

        Yields:
            A database cursor
        """
        with self.get_connection(pool_name=pool_name, for_write=for_write) as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                if for_write:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def execute_read(self, query: str, params: Optional[Dict[str, Any]] = None,
                    cursor_factory=DictCursor, pool_name: str = "default") -> List[Dict[str, Any]]:
        """
        Execute a read-only query.

        Args:
            query: SQL query to execute
            params: Query parameters
            cursor_factory: Cursor factory to use
            pool_name: Pool to use for this query

        Returns:
            List of query results
        """
        with self.get_cursor(cursor_factory=cursor_factory, pool_name=pool_name, for_write=False) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_write(self, query: str, params: Optional[Dict[str, Any]] = None,
                     cursor_factory=DictCursor, pool_name: str = "default") -> int:
        """
        Execute a write query.

        Args:
            query: SQL query to execute
            params: Query parameters
            cursor_factory: Cursor factory to use
            pool_name: Pool to use for this query

        Returns:
            Number of rows affected
        """
        with self.get_cursor(cursor_factory=cursor_factory, pool_name=pool_name, for_write=True) as cursor:
            cursor.execute(query, params)
            if cursor.rowcount is not None:
                return cursor.rowcount
            return 0

    def healthcheck(self) -> Dict[str, bool]:
        """
        Check the health of all connection pools.

        Returns:
            Dictionary with pool health status
        """
        health = {}
        for name, pool_info in self.pools.items():
            try:
                with self.get_cursor(pool_name=name) as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    health[name] = result is not None and result[0] == 1
            except Exception as e:
                logger.error(f"Health check failed for pool '{name}': {e}")
                health[name] = False
        return health

# Create the global database connection manager
db_manager = DatabaseConnectionManager()

@contextmanager
def get_connection(pool_name: str = "default", for_write: bool = False):
    """Get a database connection from the connection manager."""
    with db_manager.get_connection(pool_name=pool_name, for_write=for_write) as conn:
        yield conn

@contextmanager
def get_cursor(cursor_factory=DictCursor, pool_name: str = "default", for_write: bool = False):
    """Get a database cursor from the connection manager."""
    with db_manager.get_cursor(cursor_factory=cursor_factory, pool_name=pool_name, for_write=for_write) as cursor:
        yield cursor

def execute_read(query: str, params: Optional[Dict[str, Any]] = None,
                cursor_factory=DictCursor, pool_name: str = "default") -> List[Dict[str, Any]]:
    """Execute a read-only query using the connection manager."""
    return db_manager.execute_read(query, params, cursor_factory, pool_name)

def execute_write(query: str, params: Optional[Dict[str, Any]] = None,
                 cursor_factory=DictCursor, pool_name: str = "default") -> int:
    """Execute a write query using the connection manager."""
    return db_manager.execute_write(query, params, cursor_factory, pool_name)

def healthcheck() -> Dict[str, bool]:
    """Check the health of all connection pools."""
    return db_manager.healthcheck()

def close_pools():
    """Close all connection pools."""
    db_manager.close_pools()
