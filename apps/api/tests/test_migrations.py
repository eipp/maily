import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the path to allow importing project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.migrations import initialize_schema, run_migrations


class TestMigrations(unittest.TestCase):
    """Test cases for database migration functionality."""

    @patch('database.migrations.get_db_connection')
    def test_initialize_schema(self, mock_get_db_connection):
        """Test initializing the database schema."""
        # Set up mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn

        # Call the function
        initialize_schema()

        # Verify the function behavior
        mock_get_db_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        # Check for commits and closes
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        # Verify SQL execution (at least some calls were made)
        assert mock_cursor.execute.call_count > 0

    @patch('database.migrations.get_db_connection')
    @patch('database.migrations.glob.glob')
    @patch('database.migrations.os.path.basename')
    def test_run_migrations(self, mock_basename, mock_glob, mock_get_db_connection):
        """Test running migrations from files."""
        # Set up mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn

        # Mock migration files
        mock_glob.return_value = [
            'backend/migrations/001_add_indexes.sql',
            'backend/migrations/002_create_consent_tables.sql',
            'backend/migrations/003_create_plugin_tables.sql'
        ]
        mock_basename.side_effect = lambda x: os.path.basename(x)

        # Mock cursor.fetchone to simulate that migrations are not yet applied
        mock_cursor.fetchone.return_value = None

        # Call the function
        run_migrations()

        # Verify the function behavior
        mock_get_db_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        # Check for commits and closes
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify SQL execution for each migration file (plus creation of migration_history table)
        assert mock_cursor.execute.call_count >= 4

        # Check that all three migrations were applied
        self.assertEqual(mock_basename.call_count, 3)

    @patch('database.migrations.get_db_connection')
    @patch('database.migrations.glob.glob')
    def test_skip_applied_migrations(self, mock_glob, mock_get_db_connection):
        """Test that already applied migrations are skipped."""
        # Set up mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn

        # Mock migration files
        mock_glob.return_value = [
            'backend/migrations/001_add_indexes.sql',
            'backend/migrations/002_create_consent_tables.sql',
        ]

        # Mock cursor.fetchone to simulate that the first migration is already applied
        mock_cursor.fetchone.side_effect = [('001_add_indexes.sql',), None]

        # Call the function
        run_migrations()

        # Verify that we still connect and set up
        mock_get_db_connection.assert_called_once()

        # Verify SQL execution (more than just creating tables)
        assert mock_cursor.execute.call_count > 1

        # Check that we commit changes
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
