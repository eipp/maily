#!/usr/bin/env python3
"""
Simple script to initialize the database. This script avoids the complex import
structure and directly calls the initialization functions.
"""
import os, sys, time
import logging
import psycopg2
import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration - first check for DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
db_config = None

if DATABASE_URL:
    logger.info(f"Found DATABASE_URL environment variable")
    # Mask password in logs
    log_url = DATABASE_URL
    if '@' in DATABASE_URL and '//' in DATABASE_URL:
        start = DATABASE_URL.index('//') + 2
        if ':' in DATABASE_URL[start:]:
            user_end = DATABASE_URL.index(':', start)
            pass_end = DATABASE_URL.index('@', user_end)
            log_url = DATABASE_URL[:user_end+1] + "****" + DATABASE_URL[pass_end:]
    logger.info(f"Using database connection URL: {log_url}")

    try:
        # Parse the DATABASE_URL
        # Format: postgresql://user:password@host:port/dbname
        url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
        credentials = url_parts[0].split(':')
        db_user = credentials[0]
        db_password = credentials[1] if len(credentials) > 1 else None

        host_parts = url_parts[1].split('/')
        host_port = host_parts[0].split(':')
        db_host = host_port[0]
        db_port = int(host_port[1]) if len(host_port) > 1 else 5432

        db_name = host_parts[1].split('?')[0]

        # Store parsed config
        db_config = {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "dbname": db_name
        }
        logger.info(f"Extracted database parameters: Host={db_host}, Port={db_port}, DB={db_name}, User={db_user}")
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
        db_config = None

# Get the current system username (this is likely the correct user)
SYSTEM_USER = getpass.getuser()

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", SYSTEM_USER)  # Try with system username
POSTGRES_DB = os.getenv("POSTGRES_DB", "maily")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

def create_schema(conn):
    """Create database schema with tables once connected."""
    logger.info("Creating database tables...")
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        DROP TABLE IF EXISTS campaigns;
        DROP TABLE IF EXISTS user_configs;

        CREATE TABLE IF NOT EXISTS user_configs (
            user_id SERIAL PRIMARY KEY,
            model_name TEXT NOT NULL,
            api_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES user_configs(user_id),
            task TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            result JSONB,
            metadata JSONB,
            subject TEXT,
            body TEXT,
            image_url TEXT,
            analytics_data JSONB,
            personalization_data JSONB,
            delivery_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    return True

def try_connect(host, port, user=None, password=None):
    """Try to connect to PostgreSQL with the given parameters."""
    """Try to connect to PostgreSQL with the given parameters."""
    conn_params = {
        "host": host,
        "port": port,
        "dbname": POSTGRES_DB,
        "user": user or POSTGRES_USER,
    }

    # Add password if provided
    if password or POSTGRES_PASSWORD:
        conn_params["password"] = password or POSTGRES_PASSWORD

    # Build connection string for logging (without password)
    log_params = conn_params.copy()
    if "password" in log_params:
        log_params["password"] = "****"
    connection_string_parts = [f"{k}={v}" for k, v in log_params.items()]
    log_connection_string = " ".join(connection_string_parts)

    logger.info(f"Trying connection to {host}:{port} as {user}")

    try:
        # Convert dict to connection string
        connection_string = " ".join([f"{k}={v}" for k, v in conn_params.items()])
        conn = psycopg2.connect(connection_string)
        logger.info(f"Successfully connected to {host}:{port} as {conn_params['user']}")
        return conn
    except Exception as e:
        logger.warning(f"Failed to connect to {host}:{port} as {conn_params['user']}: {e}")
        return None

def try_connect_with_string(connection_string):
    """Try to connect using a full connection string."""
    logger.info(f"Trying connection with connection string")
    try:
        conn = psycopg2.connect(connection_string)
        logger.info(f"Successfully connected to {host}:{port} as {user}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to {host}:{port} as {user}: {e}")
        return None

def initialize_database():
    """Initialize the database schema with required tables."""
    logger.info("Starting database initialization...")
    logger.info(f"Current system user: {SYSTEM_USER}")

    # First try using the parsed DATABASE_URL if available
    if db_config:
        logger.info("Attempting connection using DATABASE_URL configuration...")
        conn = try_connect(
            db_config["host"],
            db_config["port"],
            db_config["user"],
            db_config["password"]
        )
        if conn:
            try:
                create_schema(conn)
                conn.close()
                return True
            except Exception as e:
                logger.error(f"Failed to create schema with DATABASE_URL config: {e}")

    # Fall back to trying various configurations
    connection_configs = [
        # Docker container with postgres user
        ("db", 5432, "postgres", "postgres"),
        # Localhost with postgres user
        ("localhost", 5432, "postgres", "postgres"),
        # System user without password
        ("localhost", 5432, SYSTEM_USER, None),
        # Different host configurations
        ("127.0.0.1", 5432, "postgres", "postgres"),
        ("localhost", 5432, "postgres", None),
        # Try one more with the system user and password
        ("localhost", 5432, SYSTEM_USER, "postgres"),
    ]

    # Add a delay before retry attempts
    if db_config:  # We already tried one connection, so add delay before retries
        logger.info("Waiting 2 seconds before trying fallback connections...")
        time.sleep(2)


    # Try each configuration until one works
    for host, port, user, password in connection_configs:
        conn = try_connect(host, port, user, password)
        if conn:
            try:
                create_schema(conn)
                conn.close()
                logger.info(f"Database schema initialized successfully with {host}:{port} as {user}")
                return True
            except Exception as e:
                logger.error(f"Failed to create schema: {e}")
                conn.close()

    logger.error("All connection attempts failed")
    return False

if __name__ == "__main__":
    success = initialize_database()
    if success:
        print("Database initialization complete!")
    else:
        print("Database initialization failed. Check logs for details.")
        exit(1)
