import os
from psycopg2 import pool
from loguru import logger
from contextlib import contextmanager

# Connection pool configuration
MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "5"))
MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "20"))

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "ivanpeychev")
POSTGRES_DB = os.getenv("POSTGRES_DB", "maily")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "6432"))  # Updated to use pgbouncer port
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Initialize the connection pool
connection_pool = pool.ThreadedConnectionPool(
    minconn=MIN_CONNECTIONS,
    maxconn=MAX_CONNECTIONS,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT
)

@contextmanager
def get_db_connection():
    """Get a database connection from the pool with automatic cleanup."""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise DatabaseError(f"Database connection failed: {str(e)}")
    finally:
        if conn:
            connection_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    """Get a database cursor with automatic cleanup."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()

class DatabaseError(Exception):
    """Exception raised for database-related errors."""
    pass

def execute_query(query, params=None, fetch=True, commit=True):
    """Execute a database query with connection pooling."""
    with get_db_cursor(commit=commit) as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return None

def execute_batch(query, params_list, commit=True):
    """Execute a batch of queries with connection pooling."""
    with get_db_cursor(commit=commit) as cursor:
        for params in params_list:
            cursor.execute(query, params)

def explain_analyze(query, params=None):
    """Run EXPLAIN ANALYZE on a query for performance analysis."""
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
    with get_db_cursor() as cursor:
        cursor.execute(explain_query, params)
        return cursor.fetchall()[0][0] 