#!/usr/bin/env python3
"""
Test script to verify database connection
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_psycopg_connection():
    """Test direct psycopg2 connection"""
    import psycopg2
    from psycopg2 import pool

    # Get database configuration from environment variables
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        logger.info(f"Found DATABASE_URL: {DATABASE_URL}")
        try:
            # Parse the DATABASE_URL
            url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
            credentials = url_parts[0].split(':')
            user = credentials[0]
            password = credentials[1] if len(credentials) > 1 else None

            host_parts = url_parts[1].split('/')
            host_port = host_parts[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 5432

            db_name = host_parts[1].split('?')[0]

            # Build connection params
            conn_params = {
                "host": host,
                "port": port,
                "dbname": db_name,
                "user": user
            }

            if password:
                conn_params["password"] = password

            # Log connection parameters (without password)
            log_params = conn_params.copy()
            if "password" in log_params:
                log_params["password"] = "****"
            logger.info(f"Connecting with parameters: {log_params}")

            # Create connection string
            conn_string = " ".join([f"{k}={v}" for k, v in conn_params.items()])

            # Try to connect
            logger.info("Attempting to connect to database...")
            conn = psycopg2.connect(conn_string)

            # Test query
            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            logger.info(f"Query result: {result}")

            # Close connection
            cur.close()
            conn.close()
            logger.info("Connection test successful!")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    else:
        logger.error("DATABASE_URL not set")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    try:
        from sqlalchemy import create_engine, text

        # Get database URL
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")
        if "schema" in db_url:
            db_url = db_url.split("?")[0]

        logger.info(f"Using SQLAlchemy with connection URL: {db_url}")

        # Create engine
        engine = create_engine(db_url)

        # Test connection
        logger.info("Testing SQLAlchemy connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"SQLAlchemy query result: {result.fetchone()}")

        logger.info("SQLAlchemy connection test successful!")
        return True
    except Exception as e:
        logger.error(f"SQLAlchemy connection error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing database connections")

    # Test psycopg2 connection
    logger.info("----- Testing psycopg2 connection -----")
    psycopg_result = test_psycopg_connection()

    # Test SQLAlchemy connection
    logger.info("\n----- Testing SQLAlchemy connection -----")
    sqlalchemy_result = test_sqlalchemy_connection()

    # Summary
    logger.info("\n----- Test Results -----")
    logger.info(f"psycopg2 connection: {'SUCCESS' if psycopg_result else 'FAILED'}")
    logger.info(f"SQLAlchemy connection: {'SUCCESS' if sqlalchemy_result else 'FAILED'}")

    if psycopg_result and sqlalchemy_result:
        logger.info("All database connections successful!")
        sys.exit(0)
    else:
        logger.error("Some database connections failed")
        sys.exit(1)
