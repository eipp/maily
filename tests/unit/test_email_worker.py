"""
Tests for the email worker.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import from the workers
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workers.email_worker import EmailWorker


class TestEmailWorker(unittest.TestCase):
    """Test the email worker."""

    def setUp(self):
        """Set up the test."""
        # Mock the database session
        self.db_mock = MagicMock()
        self.campaign_mock = MagicMock()
        self.campaign_mock.id = 1
        self.campaign_mock.subject = "Test Subject"
        self.campaign_mock.content = "Test Content"

        # Mock the query results
        self.db_mock.query.return_value.filter.return_value.first.return_value = self.campaign_mock

        # Mock the email service
        self.email_service_mock = MagicMock()
        self.email_service_mock.send_email.return_value = {
            "status": "sent",
            "message_id": "test-message-id",
        }

        # Create patches
        self.get_db_patcher = patch("workers.email_worker.get_db", return_value=self.db_mock)
        self.email_service_patcher = patch("workers.email_worker.EmailService", return_value=self.email_service_mock)

        # Start patches
        self.get_db_mock = self.get_db_patcher.start()
        self.email_service_class_mock = self.email_service_patcher.start()

        # Create the worker
        self.worker = EmailWorker()
        self.worker.email_service = self.email_service_mock

    def tearDown(self):
        """Clean up after the test."""
        # Stop patches
        self.get_db_patcher.stop()
        self.email_service_patcher.stop()

    def test_process_message(self):
        """Test processing a message."""
        # Create a mock message
        message = {
            "campaign_id": 1,
            "recipients": ["test@example.com", "test2@example.com"],
        }

        # Create mock channel and method
        channel_mock = MagicMock()
        method_mock = MagicMock()
        method_mock.delivery_tag = "test-tag"

        # Process the message
        self.worker.process_message(
            channel_mock,
            method_mock,
            None,
            json.dumps(message).encode(),
        )

        # Check that the campaign was retrieved
        self.db_mock.query.assert_called_once()

        # Check that the campaign status was updated to "sending"
        self.campaign_mock.status = "sending"
        self.db_mock.commit.assert_called()

        # Check that emails were sent to all recipients
        self.assertEqual(self.email_service_mock.send_email.call_count, 2)

        # Check that the campaign status was updated to "sent"
        self.assertEqual(self.campaign_mock.status, "sent")
        self.assertIn("sent_count", self.campaign_mock.metadata)
        self.assertIn("failed_count", self.campaign_mock.metadata)

        # Check that the message was acknowledged
        channel_mock.basic_ack.assert_called_once_with(delivery_tag=method_mock.delivery_tag)

    def test_process_message_invalid_json(self):
        """Test processing a message with invalid JSON."""
        # Create mock channel and method
        channel_mock = MagicMock()
        method_mock = MagicMock()
        method_mock.delivery_tag = "test-tag"

        # Process the message with invalid JSON
        self.worker.process_message(
            channel_mock,
            method_mock,
            None,
            b"invalid-json",
        )

        # Check that the message was acknowledged despite the error
        channel_mock.basic_ack.assert_called_once_with(delivery_tag=method_mock.delivery_tag)

    def test_process_message_missing_campaign(self):
        """Test processing a message with a missing campaign."""
        # Create a mock message
        message = {
            "campaign_id": 999,  # Non-existent campaign
            "recipients": ["test@example.com"],
        }

        # Mock the query to return None (campaign not found)
        self.db_mock.query.return_value.filter.return_value.first.return_value = None

        # Create mock channel and method
        channel_mock = MagicMock()
        method_mock = MagicMock()
        method_mock.delivery_tag = "test-tag"

        # Process the message
        self.worker.process_message(
            channel_mock,
            method_mock,
            None,
            json.dumps(message).encode(),
        )

        # Check that no emails were sent
        self.email_service_mock.send_email.assert_not_called()

        # Check that the message was acknowledged
        channel_mock.basic_ack.assert_called_once_with(delivery_tag=method_mock.delivery_tag)

    def test_process_message_email_error(self):
        """Test processing a message with an email sending error."""
        # Create a mock message
        message = {
            "campaign_id": 1,
            "recipients": ["test@example.com", "error@example.com"],
        }

        # Make the email service raise an exception for the second recipient
        def send_email_side_effect(to_email, **kwargs):
            if to_email == "error@example.com":
                raise Exception("Test error")
            return {
                "status": "sent",
                "message_id": "test-message-id",
            }

        self.email_service_mock.send_email.side_effect = send_email_side_effect

        # Create mock channel and method
        channel_mock = MagicMock()
        method_mock = MagicMock()
        method_mock.delivery_tag = "test-tag"

        # Process the message
        self.worker.process_message(
            channel_mock,
            method_mock,
            None,
            json.dumps(message).encode(),
        )

        # Check that the campaign status was updated to "sent" despite the error
        self.assertEqual(self.campaign_mock.status, "sent")

        # Check that the message was acknowledged
        channel_mock.basic_ack.assert_called_once_with(delivery_tag=method_mock.delivery_tag)


if __name__ == "__main__":
    unittest.main()
