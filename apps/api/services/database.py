import os
from contextlib import contextmanager
import getpass
import time
from loguru import logger
from psycopg2 import pool

# Import get_secret function - try both possible locations
try:
    from ..dependencies import get_secret
except ImportError:
    try:
        from dependencies import get_secret
    except ImportError:
        # Define a fallback get_secret function if not available
        def get_secret(path: str) -> dict:
            """Fallback get_secret when dependencies module not available."""
            if path == 'database':
                return {
                    'username': os.getenv("POSTGRES_USER", getpass.getuser()),
                    'password': os.getenv("POSTGRES_PASSWORD"),
                    'host': os.getenv("POSTGRES_HOST", "localhost"),
                    'port': int(os.getenv("POSTGRES_PORT", "5432")),
                    'dbname': os.getenv("POSTGRES_DB", "maily")
                }
            return {}

# Connection pool configuration
MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "5"))
MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "20"))

# First try to get database credentials from Vault
try:
    db_secrets = get_secret('database')
    POSTGRES_USER = db_secrets.get('username')
    POSTGRES_PASSWORD = db_secrets.get('password')
    POSTGRES_HOST = db_secrets.get('host')
    POSTGRES_PORT = db_secrets.get('port')
    POSTGRES_DB = db_secrets.get('dbname')
    logger.info(f"Retrieved database credentials from Vault: Host={POSTGRES_HOST}, Port={POSTGRES_PORT}, DB={POSTGRES_DB}, User={POSTGRES_USER}")
except Exception as e:
    logger.warning(f"Failed to retrieve database credentials from Vault: {e}")
    logger.warning("Falling back to environment variables for database connection")

    # Fallback - First try to extract from DATABASE_URL if available
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        # Parse the DATABASE_URL
        logger.info(f"Found DATABASE_URL: {DATABASE_URL}")
        # Mask the password in the log
        log_url = DATABASE_URL
        if '@' in DATABASE_URL and '//' in DATABASE_URL:
            start = DATABASE_URL.index('//') + 2
            if ':' in DATABASE_URL[start:]:
                user_end = DATABASE_URL.index(':', start)
                pass_end = DATABASE_URL.index('@', user_end)
                log_url = DATABASE_URL[:user_end+1] + "****" + DATABASE_URL[pass_end:]
        logger.info(f"Using database connection URL: {log_url}")

        try:
            # Extract credentials from URL
            # Format: postgresql://user:password@host:port/dbname
            url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
            credentials = url_parts[0].split(':')
            POSTGRES_USER = credentials[0]
            POSTGRES_PASSWORD = credentials[1] if len(credentials) > 1 else None

            host_parts = url_parts[1].split('/')
            host_port = host_parts[0].split(':')
            POSTGRES_HOST = host_port[0]
            POSTGRES_PORT = int(host_port[1]) if len(host_port) > 1 else 5432

            POSTGRES_DB = host_parts[1].split('?')[0]
            logger.info(f"Extracted database parameters from URL: Host={POSTGRES_HOST}, Port={POSTGRES_PORT}, DB={POSTGRES_DB}, User={POSTGRES_USER}")
        except Exception as e:
            logger.error(f"Failed to parse DATABASE_URL: {e}")
            # Fall back to separate environment variables
            SYSTEM_USER = getpass.getuser()
            POSTGRES_USER = os.getenv("POSTGRES_USER", SYSTEM_USER)
            POSTGRES_DB = os.getenv("POSTGRES_DB", "maily")
            POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
            POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
            POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    else:
        # Use separate environment variables
        SYSTEM_USER = getpass.getuser()
        POSTGRES_USER = os.getenv("POSTGRES_USER", SYSTEM_USER)
        POSTGRES_DB = os.getenv("POSTGRES_DB", "maily")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Log the final connection parameters (without password)
logger.info(f"Database connection parameters: Host={POSTGRES_HOST}, Port={POSTGRES_PORT}, DB={POSTGRES_DB}, User={POSTGRES_USER}, Password={'*****' if POSTGRES_PASSWORD else 'Not Set'}")

if not POSTGRES_PASSWORD:
    logger.warning("Database password is not set")

# Initialize the connection pool
logger.info("Initializing database connection pool...")
connection_pool = pool.ThreadedConnectionPool(
    minconn=MIN_CONNECTIONS,
    maxconn=MAX_CONNECTIONS,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    password=POSTGRES_PASSWORD
)
logger.info("Database connection pool initialized")

def wait_for_db(max_attempts=5, interval=2):
    """Wait for database to become available, with retries."""
    attempt = 0
    while attempt < max_attempts:
        try:
            conn = connection_pool.getconn()
            logger.info("Database is available!")
            connection_pool.putconn(conn)
            return True
        except Exception as e:
            attempt += 1
            logger.warning(f"Database not available (attempt {attempt}/{max_attempts}): {e}")
            if attempt < max_attempts:
                time.sleep(interval)
    return False

@contextmanager
def get_db_connection():
    """Get a database connection from the pool with automatic cleanup."""
    conn = None
    conn_error = None
    try:
        # Attempt to connect to the database
        logger.debug("Attempting to get database connection from pool")
        conn = connection_pool.getconn()
        logger.debug("Successfully acquired database connection")
        yield conn
    except Exception as e:
        conn_error = str(e)
        logger.error(f"Database connection failed: {conn_error}")
        raise DatabaseError(f"Database connection failed: {conn_error}")
    finally:
        if conn:
            logger.debug("Returning connection to pool")
            connection_pool.putconn(conn)
        elif not conn_error:
            logger.error("Failed to get connection from pool")
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
