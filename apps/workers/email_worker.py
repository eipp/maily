"""
Email worker for processing email campaigns asynchronously.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional

import pika
from pika.exceptions import AMQPConnectionError, ChannelClosedByBroker

from database import get_db
from models import Campaign, Email
from services.campaign_service import CampaignService
from services.email_service import EmailService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Queue names
CAMPAIGN_QUEUE = "campaign_queue"
EMAIL_QUEUE = "email_queue"
ANALYTICS_QUEUE = "analytics_queue"

# RabbitMQ connection parameters
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


class EmailWorker:
    """Worker for processing email campaigns asynchronously."""

    def __init__(self):
        """Initialize the worker."""
        self.connection = None
        self.channel = None
        self.campaign_service = CampaignService(next(get_db()))
        self.email_service = EmailService()

    def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            # Connect to RabbitMQ
            self.connection = pika.BlockingConnection(
                pika.URLParameters(RABBITMQ_URL)
            )
            self.channel = self.connection.channel()

            # Declare queues
            self.channel.queue_declare(queue=CAMPAIGN_QUEUE, durable=True)
            self.channel.queue_declare(queue=EMAIL_QUEUE, durable=True)
            self.channel.queue_declare(queue=ANALYTICS_QUEUE, durable=True)

            logger.info("Connected to RabbitMQ")
        except AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            time.sleep(5)
            self.connect()

    def start(self) -> None:
        """Start the worker."""
        self.connect()

        # Set up consumers
        self.channel.basic_consume(
            queue=CAMPAIGN_QUEUE,
            on_message_callback=self.process_campaign,
            auto_ack=False,
        )
        self.channel.basic_consume(
            queue=EMAIL_QUEUE,
            on_message_callback=self.process_email,
            auto_ack=False,
        )

        logger.info("Worker started. Waiting for messages...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
            logger.info("Worker stopped")
        except Exception as e:
            logger.error(f"Error in worker: {e}")
            self.connection.close()
            time.sleep(5)
            self.start()

    def process_campaign(
        self, ch, method, properties, body
    ) -> None:
        """Process a campaign message."""
        try:
            # Parse message
            message = json.loads(body)
            campaign_id = message.get("campaign_id")
            recipients = message.get("recipients", [])

            logger.info(f"Processing campaign {campaign_id} with {len(recipients)} recipients")

            # Get campaign from database
            campaign = self.campaign_service.get_campaign(campaign_id)
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Update campaign status
            self.campaign_service.update_campaign(
                campaign_id, {"status": "processing"}
            )

            # Process each recipient
            for recipient in recipients:
                # Create email message
                email_message = {
                    "campaign_id": campaign_id,
                    "recipient": recipient,
                    "subject": campaign.subject,
                    "content": campaign.content,
                }

                # Publish to email queue
                self.channel.basic_publish(
                    exchange="",
                    routing_key=EMAIL_QUEUE,
                    body=json.dumps(email_message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                    ),
                )

            # Update campaign status
            self.campaign_service.update_campaign(
                campaign_id, {"status": "sent"}
            )

            logger.info(f"Campaign {campaign_id} processed successfully")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing campaign: {e}")
            # Negative acknowledgment to requeue the message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def process_email(
        self, ch, method, properties, body
    ) -> None:
        """Process an email message."""
        try:
            # Parse message
            message = json.loads(body)
            campaign_id = message.get("campaign_id")
            recipient = message.get("recipient")
            subject = message.get("subject")
            content = message.get("content")

            logger.info(f"Sending email to {recipient} for campaign {campaign_id}")

            # Send email
            result = self.email_service.send_email(
                to_email=recipient,
                subject=subject,
                content=content,
            )

            # Create email record in database
            db = next(get_db())
            email = Email(
                campaign_id=campaign_id,
                recipient=recipient,
                message_id=result.get("message_id"),
                status="sent",
            )
            db.add(email)
            db.commit()

            # Publish analytics event
            analytics_message = {
                "campaign_id": campaign_id,
                "email_id": email.id,
                "message_id": result.get("message_id"),
                "event": "sent",
                "timestamp": time.time(),
            }
            self.channel.basic_publish(
                exchange="",
                routing_key=ANALYTICS_QUEUE,
                body=json.dumps(analytics_message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ),
            )

            logger.info(f"Email sent to {recipient} for campaign {campaign_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            # Negative acknowledgment to requeue the message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


if __name__ == "__main__":
    worker = EmailWorker()
    worker.start()
