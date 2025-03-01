from loguru import logger
import os
import glob
from typing import List
import sys

# Add the parent directory to the path for direct imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Direct import from services
from services.database import get_db_connection, get_db_cursor


def initialize_schema():
    """Initialize database schema with required tables."""
    try:
        # Use get_db_cursor context manager for proper connection handling
        with get_db_cursor(commit=True) as cur:
            # Create tables
            logger.info("Creating database tables...")
            cur.execute(
                """
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
            """
            )
            logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {str(e)}")
        raise


def run_migrations():
    """Run all migrations in order to update the database schema."""
    try:
        logger.info("Starting database migrations...")
        # Get all migration files in order
        migration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
        migration_files = sorted(glob.glob(os.path.join(migration_path, '*.sql')))

        if not migration_files:
            logger.info(f"No migration files found in {migration_path}")
            return

        # First, create migration history table if it doesn't exist
        logger.info("Creating migration history table if it doesn't exist...")
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        # Get list of applied migrations
        logger.info("Checking for already applied migrations...")
        applied_migrations = set()
        with get_db_cursor() as cur:
            cur.execute("SELECT migration_name FROM migration_history")
            applied_migrations = {row[0] for row in cur.fetchall()}

        logger.info(f"Found {len(applied_migrations)} already applied migrations")

        # Apply each migration that hasn't been applied yet
        for migration_file in migration_files:
            migration_name = os.path.basename(migration_file)

            if migration_name in applied_migrations:
                logger.info(f"Migration {migration_name} already applied, skipping")
                continue

            logger.info(f"Applying migration: {migration_name}")

            # Read and execute migration file
            with open(migration_file, 'r') as f:
                migration_sql = f.read()

            # Execute the migration in a transaction
            try:
                with get_db_cursor(commit=True) as cur:
                    # Execute migration SQL
                    cur.execute(migration_sql)

                    # Record migration as applied
                    cur.execute(
                        "INSERT INTO migration_history (migration_name) VALUES (%s)",
                        (migration_name,)
                    )

                logger.info(f"Successfully applied migration: {migration_name}")
            except Exception as e:
                logger.error(f"Failed to apply migration {migration_name}: {str(e)}")
                raise

        logger.info("All migrations applied successfully")
    except Exception as e:
        logger.error(f"Migration process failed: {str(e)}")
        raise
