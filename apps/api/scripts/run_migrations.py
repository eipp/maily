#!/usr/bin/env python
"""
Database migration script for Maily.

This script runs all database migrations in the migrations directory
to keep the database schema up to date.
"""

import os
import sys
import argparse
from loguru import logger

# Add parent directory to path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.migrations import initialize_schema, run_migrations
from config.settings import get_settings

settings = get_settings()


def configure_logging():
    """Configure logging for the migration script."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    logger.add(
        "logs/migrations.log",
        format=settings.LOG_FORMAT,
        level="INFO",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
    )


def main():
    """Run database migrations."""
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema (warning: this may reset data)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    configure_logging()
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG", colorize=True)

    try:
        logger.info("Starting database migration process")

        if args.init:
            logger.warning("Initializing database schema (this may reset data)")
            initialize_schema()

        # Run migrations
        run_migrations()

        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
