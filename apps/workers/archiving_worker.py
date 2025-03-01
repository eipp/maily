"""
Archiving Worker Module.

This worker handles archiving of old data to maintain database performance.
It moves old data from the primary database to the archive database.
"""
import logging
import os
import signal
import sys
import time
import threading
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta

from sqlalchemy import create_engine, MetaData, Table, select, insert, delete
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import backend modules - adjust the path as needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config.database_config import (
    DATABASE_URL, ARCHIVE_DATABASE_URL, ARCHIVE_THRESHOLD_DAYS, ARCHIVE_BATCH_SIZE,
    should_archive_record
)
from backend.utils.db_session import get_primary_session, get_archive_session

# Global state for tracking
running = True

# Tables to archive and their date columns
ARCHIVE_TABLES = {
    "emails": "sent_at",
    "tracking_events": "timestamp",
    "campaigns": "completed_at",
}

class ArchivingWorker:
    """Worker for archiving old data to maintain database performance."""

    def __init__(self):
        """Initialize the archiving worker."""
        self.primary_engine = create_engine(DATABASE_URL)
        self.archive_engine = create_engine(ARCHIVE_DATABASE_URL)
        self.primary_metadata = MetaData()
        self.archive_metadata = MetaData()
        self.primary_metadata.reflect(bind=self.primary_engine)
        self.archive_metadata.reflect(bind=self.archive_engine)

    def start(self):
        """Start the worker."""
        logger.info("Starting Archiving Worker")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            # Ensure archive tables exist
            self._ensure_archive_tables()

            # Run archiving process
            self._run_archiving()

        except Exception as e:
            logger.error(f"Error in archiving worker: {e}")
        finally:
            logger.info("Archiving Worker shut down")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        global running
        logger.info(f"Received signal {signum}, shutting down")
        running = False

    def _ensure_archive_tables(self):
        """Ensure archive tables exist in the archive database."""
        # Create tables in archive database if they don't exist
        for table_name in ARCHIVE_TABLES.keys():
            if table_name in self.primary_metadata.tables and table_name not in self.archive_metadata.tables:
                # Get table from primary database
                primary_table = self.primary_metadata.tables[table_name]

                # Create table in archive database
                primary_table.tometadata(self.archive_metadata).create(self.archive_engine)
                logger.info(f"Created archive table: {table_name}")

    def _run_archiving(self):
        """Run the archiving process."""
        while running:
            try:
                # Archive each table
                for table_name, date_column in ARCHIVE_TABLES.items():
                    self._archive_table(table_name, date_column)

                # Sleep for a while before next archiving run
                logger.info("Archiving cycle completed, sleeping for 1 hour")
                for _ in range(60):  # Check for shutdown signal every minute
                    if not running:
                        break
                    time.sleep(60)

            except Exception as e:
                logger.error(f"Error during archiving: {e}")
                time.sleep(300)  # Sleep for 5 minutes on error

    def _archive_table(self, table_name: str, date_column: str):
        """
        Archive old records from a table.

        Args:
            table_name: Name of the table to archive
            date_column: Name of the date column to use for archiving
        """
        logger.info(f"Archiving table: {table_name}")

        # Get tables
        if table_name not in self.primary_metadata.tables:
            logger.warning(f"Table {table_name} not found in primary database")
            return

        if table_name not in self.archive_metadata.tables:
            logger.warning(f"Table {table_name} not found in archive database")
            return

        primary_table = self.primary_metadata.tables[table_name]
        archive_table = self.archive_metadata.tables[table_name]

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=ARCHIVE_THRESHOLD_DAYS)

        # Get primary and archive sessions
        primary_session = get_primary_session()
        archive_session = get_archive_session()

        try:
            # Find records to archive
            date_col = getattr(primary_table.c, date_column)
            query = select([primary_table]).where(date_col < cutoff_date).limit(ARCHIVE_BATCH_SIZE)

            # Execute query
            result = primary_session.execute(query)
            records = result.fetchall()

            if not records:
                logger.info(f"No records to archive in {table_name}")
                return

            logger.info(f"Archiving {len(records)} records from {table_name}")

            # Begin transaction
            archive_session.begin()
            primary_session.begin()

            try:
                # Insert records into archive database
                for record in records:
                    # Convert record to dictionary
                    record_dict = dict(record)

                    # Insert into archive database
                    archive_session.execute(
                        archive_table.insert().values(**record_dict)
                    )

                # Delete records from primary database
                for record in records:
                    # Get primary key columns
                    pk_cols = [col for col in primary_table.primary_key.columns]

                    # Build where clause for primary key
                    where_clause = []
                    for col in pk_cols:
                        where_clause.append(col == record[col.name])

                    # Delete from primary database
                    primary_session.execute(
                        primary_table.delete().where(*where_clause)
                    )

                # Commit transactions
                archive_session.commit()
                primary_session.commit()

                logger.info(f"Successfully archived {len(records)} records from {table_name}")

            except Exception as e:
                # Rollback transactions on error
                archive_session.rollback()
                primary_session.rollback()
                logger.error(f"Error archiving records from {table_name}: {e}")
                raise

        except Exception as e:
            logger.error(f"Error querying records from {table_name}: {e}")
        finally:
            primary_session.close()
            archive_session.close()

def main():
    """Main entry point for the worker."""
    worker = ArchivingWorker()
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Archiving worker interrupted, shutting down")

if __name__ == "__main__":
    main()
