"""
Database Connection Pool Manager

Provides optimized connection pooling for database access with monitoring,
retry mechanisms, and query optimization.
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Callable, TypeVar, Generic, Union
from contextlib import contextmanager
import functools
import re

# SQLAlchemy imports
from sqlalchemy import create_engine, event, text, Column, func, desc, asc, select, update, delete
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import SQLAlchemyError, DBAPIError, OperationalError, DisconnectionError

# Metrics libraries (if available)
try:
    import prometheus_client as prom
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# For type hints
T = TypeVar('T')

# Setup logger
logger = logging.getLogger(__name__)

# Database metrics
if PROMETHEUS_AVAILABLE:
    DB_POOL_SIZE = prom.Gauge('db_pool_size', 'Current database connection pool size')
    DB_POOL_CHECKED_OUT = prom.Gauge('db_pool_checked_out', 'Current checked out connections')
    DB_POOL_OVERFLOW = prom.Gauge('db_pool_overflow', 'Current overflow connections')

    DB_QUERY_COUNTER = prom.Counter('db_query_count', 'Database query count', ['operation', 'table'])
    DB_QUERY_LATENCY = prom.Histogram('db_query_latency_seconds', 'Database query latency in seconds',
                                      ['operation', 'table'], buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10))
    DB_ERROR_COUNTER = prom.Counter('db_error_count', 'Database error count', ['error_type'])
    DB_CONNECTION_ERRORS = prom.Counter('db_connection_errors', 'Database connection errors')
    DB_RETRIES = prom.Counter('db_query_retries', 'Database query retries')


class QueryMetrics:
    """Store and calculate query metrics."""

    def __init__(self):
        """Initialize metrics storage."""
        self.query_counts: Dict[str, int] = {}
        self.query_times: Dict[str, List[float]] = {}
        self.query_tables: Dict[str, str] = {}
        self.slow_queries: List[Tuple[str, float]] = []
        self.error_counts: Dict[str, int] = {}
        self.lock = threading.RLock()

    def record_query(self, query: str, execution_time: float):
        """Record a query execution."""
        with self.lock:
            # Normalize query for better grouping
            normalized_query = self._normalize_query(query)

            # Extract table name
            table = self._extract_table(query)

            # Record metrics
            if normalized_query not in self.query_counts:
                self.query_counts[normalized_query] = 0
                self.query_times[normalized_query] = []
                self.query_tables[normalized_query] = table

            self.query_counts[normalized_query] += 1
            self.query_times[normalized_query].append(execution_time)

            # Track slow queries (over 100ms)
            if execution_time > 0.1:
                self.slow_queries.append((normalized_query, execution_time))
                # Keep only the 100 slowest queries
                self.slow_queries.sort(key=lambda x: x[1], reverse=True)
                if len(self.slow_queries) > 100:
                    self.slow_queries.pop()

    def record_error(self, error_type: str):
        """Record a database error."""
        with self.lock:
            if error_type not in self.error_counts:
                self.error_counts[error_type] = 0
            self.error_counts[error_type] += 1

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get the slowest queries."""
        with self.lock:
            return [
                {
                    "query": query,
                    "time": time,
                    "table": self.query_tables.get(query, "unknown")
                }
                for query, time in self.slow_queries
            ]

    def get_most_frequent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most frequently executed queries."""
        with self.lock:
            sorted_queries = sorted(
                self.query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]

            return [
                {
                    "query": query,
                    "count": count,
                    "avg_time": sum(self.query_times[query]) / len(self.query_times[query]),
                    "table": self.query_tables.get(query, "unknown")
                }
                for query, count in sorted_queries
            ]

    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        with self.lock:
            return self.error_counts.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of query metrics."""
        with self.lock:
            total_queries = sum(self.query_counts.values())
            total_errors = sum(self.error_counts.values())
            all_times = [
                time for times in self.query_times.values() for time in times
            ]

            return {
                "total_queries": total_queries,
                "total_errors": total_errors,
                "avg_query_time": sum(all_times) / len(all_times) if all_times else 0,
                "max_query_time": max(all_times) if all_times else 0,
                "error_rate": total_errors / total_queries if total_queries > 0 else 0,
                "tables": list(set(self.query_tables.values())),
                "slow_query_count": len(self.slow_queries)
            }

    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.query_counts.clear()
            self.query_times.clear()
            self.query_tables.clear()
            self.slow_queries.clear()
            self.error_counts.clear()

    def _normalize_query(self, query: str) -> str:
        """Normalize a query by removing specific values."""
        # Convert to lowercase for case-insensitive comparison
        query = query.lower()

        # Replace specific values in WHERE clauses
        query = re.sub(r"(where\s+\w+\s*=\s*)('[^']*'|\d+)", r"\1?", query)
        query = re.sub(r"(where\s+\w+\s*in\s*\()([^)]*)", r"\1?", query)

        # Replace LIMIT/OFFSET values
        query = re.sub(r"(limit\s+)\d+", r"\1?", query)
        query = re.sub(r"(offset\s+)\d+", r"\1?", query)

        return query

    def _extract_table(self, query: str) -> str:
        """Extract the main table name from a query."""
        # Simple regex to extract table name from common queries
        select_match = re.search(r"from\s+([a-zA-Z0-9_]+)", query.lower())
        update_match = re.search(r"update\s+([a-zA-Z0-9_]+)", query.lower())
        insert_match = re.search(r"insert\s+into\s+([a-zA-Z0-9_]+)", query.lower())
        delete_match = re.search(r"delete\s+from\s+([a-zA-Z0-9_]+)", query.lower())

        if select_match:
            return select_match.group(1)
        elif update_match:
            return update_match.group(1)
        elif insert_match:
            return insert_match.group(1)
        elif delete_match:
            return delete_match.group(1)

        return "unknown"


class OptimizedQueryGenerator:
    """Generate optimized SQL queries."""

    @staticmethod
    def add_query_hint(query: str, hint: str) -> str:
        """Add optimizer hint to a query."""
        # Add hint after SELECT
        if query.upper().startswith("SELECT"):
            return query.replace("SELECT", f"SELECT {hint}", 1)
        return query

    @staticmethod
    def optimize_for_count(query: str) -> str:
        """Optimize a query for COUNT operations."""
        # Use COUNT(*) instead of COUNT(column) when possible
        query = re.sub(r"COUNT\(\s*DISTINCT\s+\w+\s*\)", "COUNT(DISTINCT ?)", query, flags=re.IGNORECASE)
        query = re.sub(r"COUNT\(\s*\w+\s*\)", "COUNT(*)", query, flags=re.IGNORECASE)

        # Add index hint for PostgreSQL
        if query.upper().startswith("SELECT") and "COUNT" in query.upper():
            query = OptimizedQueryGenerator.add_query_hint(query, "/*+ IndexScan */")

        return query

    @staticmethod
    def optimize_pagination(query: str, limit: int, offset: int) -> str:
        """Optimize a query for pagination."""
        # Use OFFSET with LIMIT for PostgreSQL
        if query.upper().startswith("SELECT") and "ORDER BY" in query.upper():
            # Check if LIMIT/OFFSET already exists
            if "LIMIT" not in query.upper():
                query = f"{query} LIMIT {limit}"
            if "OFFSET" not in query.upper():
                query = f"{query} OFFSET {offset}"

        return query

    @staticmethod
    def optimize_in_clause(query: str, values: List[Any]) -> str:
        """Optimize a query with IN clause."""
        # For small lists, use IN clause
        if len(values) <= 100:
            placeholders = ", ".join(["?"] * len(values))
            return query.replace("IN (?)", f"IN ({placeholders})")

        # For large lists, recommend using temporary table or JOIN
        logger.warning(f"Large IN clause with {len(values)} values. Consider using a temporary table.")
        return query


class DatabaseConnectionPool:
    """
    Optimized database connection pool manager.

    Features:
    - Connection pooling with monitoring
    - Query timing and optimization
    - Automatic retry for transient errors
    - Connection health checks
    - Metrics collection
    """

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        pool_timeout: int = 30,
        query_timeout: int = 60,
        application_name: str = "maily-api",
        enable_metrics: bool = True,
        enable_slow_query_logging: bool = True,
        slow_query_threshold: float = 0.5,  # seconds
        max_retries: int = 3,
        retry_delay: float = 0.1,  # seconds
    ):
        """
        Initialize the database connection pool.

        Args:
            connection_string: Database connection string
            pool_size: Base number of connections to keep open
            max_overflow: Maximum number of additional connections
            pool_recycle: Seconds after which a connection is recycled
            pool_pre_ping: Whether to check connection health before use
            pool_timeout: Seconds to wait for a connection from the pool
            query_timeout: Seconds to wait for a query to complete
            application_name: Name to identify this application in the database
            enable_metrics: Whether to collect query metrics
            enable_slow_query_logging: Whether to log slow queries
            slow_query_threshold: Threshold in seconds for slow query logging
            max_retries: Maximum number of retries for failed queries
            retry_delay: Delay between retries in seconds
        """
        # Augment connection string with application name for tracking
        connection_parts = connection_string.split("?")
        base_connection = connection_parts[0]
        params = connection_parts[1] if len(connection_parts) > 1 else ""

        # Add application name
        if "postgresql" in connection_string:
            if params:
                params += f"&application_name={application_name}"
            else:
                params = f"application_name={application_name}"

        final_connection_string = f"{base_connection}?{params}" if params else base_connection

        # Create engine with optimized pool settings
        self.engine = create_engine(
            final_connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            pool_timeout=pool_timeout,
            connect_args={"options": f"-c statement_timeout={query_timeout * 1000}"}
            if "postgresql" in connection_string
            else {},
        )

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        # Store configuration
        self.query_timeout = query_timeout
        self.enable_metrics = enable_metrics
        self.enable_slow_query_logging = enable_slow_query_logging
        self.slow_query_threshold = slow_query_threshold
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize metrics
        self.metrics = QueryMetrics() if enable_metrics else None

        # Set up event listeners
        self._setup_event_listeners()

        logger.info(f"Initialized database connection pool with size {pool_size}, max overflow {max_overflow}")

    def _setup_event_listeners(self):
        """Set up event listeners for the connection pool."""
        # Update pool stats
        @event.listens_for(self.engine, "connect")
        def connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")
            if PROMETHEUS_AVAILABLE:
                DB_POOL_SIZE.set(self.engine.pool.size())
                DB_POOL_CHECKED_OUT.set(self.engine.pool.checkedout())
                DB_POOL_OVERFLOW.set(self.engine.pool.overflow())

        @event.listens_for(self.engine, "checkout")
        def checkout(dbapi_connection, connection_record, connection_proxy):
            if PROMETHEUS_AVAILABLE:
                DB_POOL_CHECKED_OUT.set(self.engine.pool.checkedout())

        @event.listens_for(self.engine, "checkin")
        def checkin(dbapi_connection, connection_record):
            if PROMETHEUS_AVAILABLE:
                DB_POOL_CHECKED_OUT.set(self.engine.pool.checkedout())

        @event.listens_for(self.engine, "close")
        def close(dbapi_connection, connection_record):
            logger.debug("Database connection closed")
            if PROMETHEUS_AVAILABLE:
                DB_POOL_SIZE.set(self.engine.pool.size())

        # Query timing
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            if self.enable_metrics and hasattr(self, 'metrics') and self.metrics:
                operation = statement.split()[0].lower() if statement.split() else "unknown"
                table = self.metrics._extract_table(statement)
                if PROMETHEUS_AVAILABLE:
                    DB_QUERY_COUNTER.labels(operation=operation, table=table).inc()

        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop()

            # Log slow queries
            if self.enable_slow_query_logging and total_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected ({total_time:.2f}s): {statement}")

            # Record metrics
            if self.enable_metrics and hasattr(self, 'metrics') and self.metrics:
                self.metrics.record_query(statement, total_time)

                operation = statement.split()[0].lower() if statement.split() else "unknown"
                table = self.metrics._extract_table(statement)

                if PROMETHEUS_AVAILABLE:
                    DB_QUERY_LATENCY.labels(operation=operation, table=table).observe(total_time)

    @contextmanager
    def session(self):
        """
        Context manager for database sessions with automatic retry.

        Yields:
            SQLAlchemy session

        Example:
            with db_pool.session() as session:
                result = session.query(User).all()
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()

            # Record error metrics
            error_type = type(e).__name__
            if self.enable_metrics and hasattr(self, 'metrics') and self.metrics:
                self.metrics.record_error(error_type)

                if PROMETHEUS_AVAILABLE:
                    DB_ERROR_COUNTER.labels(error_type=error_type).inc()

            # Log the error
            logger.error(f"Database error: {str(e)}")

            # Reraise the exception
            raise
        finally:
            session.close()

    def execute_with_retry(self, func, *args, max_retries=None, **kwargs):
        """
        Execute a database function with automatic retry for transient errors.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            max_retries: Override default max retries
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            Exception: If all retries fail
        """
        retries = 0
        max_attempts = max_retries if max_retries is not None else self.max_retries
        last_error = None

        while retries <= max_attempts:
            try:
                if retries > 0:
                    # Exponential backoff
                    backoff_time = self.retry_delay * (2 ** (retries - 1))
                    logger.info(f"Retrying database operation (attempt {retries}/{max_attempts})")
                    time.sleep(backoff_time)

                    if PROMETHEUS_AVAILABLE:
                        DB_RETRIES.inc()

                # Execute the function
                with self.session() as session:
                    result = func(session, *args, **kwargs)
                    return result

            except (OperationalError, DisconnectionError) as e:
                # Retry on connection errors
                retries += 1
                last_error = e

                logger.warning(f"Database connection error (will retry): {str(e)}")

                if PROMETHEUS_AVAILABLE:
                    DB_CONNECTION_ERRORS.inc()

                if retries > max_attempts:
                    break
            except Exception as e:
                # Don't retry on other errors
                raise

        # If we get here, all retries failed
        logger.error(f"Database operation failed after {max_attempts} retries: {str(last_error)}")
        raise last_error

    def get_connection_stats(self):
        """
        Get statistics about the connection pool.

        Returns:
            Dict with connection statistics
        """
        stats = {
            "pool_size": self.engine.pool.size(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow(),
        }

        if self.enable_metrics and hasattr(self, 'metrics') and self.metrics:
            stats["query_stats"] = self.metrics.get_summary()
            stats["slow_queries"] = self.metrics.get_slow_queries()
            stats["frequent_queries"] = self.metrics.get_most_frequent_queries()
            stats["errors"] = self.metrics.get_error_stats()

        return stats

    def optimize_table(self, table_name: str):
        """
        Run database optimization on a table.

        Args:
            table_name: Name of the table to optimize
        """
        with self.session() as session:
            # For PostgreSQL
            if "postgresql" in str(self.engine.url):
                # Analyze to update statistics
                session.execute(text(f"ANALYZE {table_name}"))
                # Vacuum to reclaim space
                session.execute(text(f"VACUUM {table_name}"))
                logger.info(f"Optimized table {table_name} (analyze, vacuum)")

            # For MySQL
            elif "mysql" in str(self.engine.url):
                session.execute(text(f"OPTIMIZE TABLE {table_name}"))
                logger.info(f"Optimized table {table_name}")

            # For SQLite
            elif "sqlite" in str(self.engine.url):
                session.execute(text("PRAGMA optimize"))
                logger.info(f"Optimized database")

    def add_index(self, table_name: str, column_name: str, index_name: Optional[str] = None):
        """
        Add an index to a table.

        Args:
            table_name: Name of the table
            column_name: Name of the column to index
            index_name: Optional name for the index
        """
        index_name = index_name or f"idx_{table_name}_{column_name}"

        with self.session() as session:
            # Check if index already exists
            if "postgresql" in str(self.engine.url):
                result = session.execute(
                    text(f"SELECT 1 FROM pg_indexes WHERE tablename = '{table_name}' AND indexname = '{index_name}'")
                ).scalar()

                if not result:
                    session.execute(text(f"CREATE INDEX {index_name} ON {table_name} ({column_name})"))
                    logger.info(f"Created index {index_name} on {table_name}({column_name})")
            else:
                # For other databases, just try to create it
                try:
                    session.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})"))
                    logger.info(f"Created index {index_name} on {table_name}({column_name})")
                except SQLAlchemyError as e:
                    logger.warning(f"Failed to create index: {str(e)}")

    def check_missing_indexes(self):
        """
        Check for missing indexes based on query patterns.

        Returns:
            List of table/column combinations that might benefit from indexing
        """
        if not self.enable_metrics or not hasattr(self, 'metrics') or not self.metrics:
            return []

        suggestions = []

        # Get frequent queries
        frequent_queries = self.metrics.get_most_frequent_queries(limit=20)

        # Analyze queries for WHERE clauses without indexes
        for query_info in frequent_queries:
            query = query_info["query"]
            table = query_info["table"]

            # Simple heuristic: look for WHERE clauses
            where_matches = re.findall(r"where\s+(\w+\.\w+|\w+)\s*=", query, re.IGNORECASE)
            for match in where_matches:
                if "." in match:
                    table_alias, column = match.split(".")
                else:
                    column = match

                # Skip ID columns as they're likely already indexed
                if column.lower() == "id":
                    continue

                suggestions.append({
                    "table": table,
                    "column": column,
                    "query_count": query_info["count"],
                    "query": query
                })

        return suggestions

    def close(self):
        """Close the connection pool."""
        self.engine.dispose()
        logger.info("Database connection pool closed")


# Create a decorator for database operations
def db_operation(func=None, max_retries=None, read_only=False):
    """
    Decorator for database operations with automatic retry.

    Args:
        func: Function to decorate
        max_retries: Maximum number of retries (None for default)
        read_only: Whether this is a read-only operation

    Returns:
        Decorated function

    Example:
        @db_operation(max_retries=5)
        def get_user(session, user_id):
            return session.query(User).filter(User.id == user_id).first()
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(db_pool, *args, **kwargs):
            return db_pool.execute_with_retry(f, *args, max_retries=max_retries, **kwargs)
        return wrapper

    if func is None:
        return decorator
    return decorator(func)


# Default database connection pool
_default_pool = None

def get_db_pool(
    connection_string: Optional[str] = None,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
) -> DatabaseConnectionPool:
    """
    Get or create the default database connection pool.

    Args:
        connection_string: Database connection string (only used if pool doesn't exist)
        pool_size: Pool size (only used if pool doesn't exist)
        max_overflow: Max overflow (only used if pool doesn't exist)

    Returns:
        DatabaseConnectionPool instance
    """
    global _default_pool

    if _default_pool is None:
        if connection_string is None:
            connection_string = os.environ.get("DATABASE_URL")
            if not connection_string:
                raise ValueError("No database connection string provided")

        _default_pool = DatabaseConnectionPool(
            connection_string=connection_string,
            pool_size=pool_size or 5,
            max_overflow=max_overflow or 10
        )

    return _default_pool
