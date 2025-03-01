"""
Queue Manager for setting up and managing RabbitMQ queues.
Handles creating exchanges, queues, and managing connections.
"""
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from backend.config.queue_config import (
    RABBITMQ_URL, QUEUE_CONFIGS, DLX_CONFIG, DLX_QUEUE, RATE_LIMITS, Queues
)

logger = logging.getLogger(__name__)

class QueueManager:
    """
    Manager for RabbitMQ queues, exchanges, and connections.
    Handles automatic reconnection, queue setup, and message publication.
    """
    def __init__(self, connection_url: str = RABBITMQ_URL):
        self.connection_url = connection_url
        self.connection = None
        self.channel = None
        self._is_connected = False
        self._reconnect_delay = 0
        self._connection_lock = threading.Lock()
        self._last_message_time = {}
        self._setup_exchanges_and_queues()

    def _get_connection_parameters(self) -> pika.ConnectionParameters:
        """Get connection parameters for RabbitMQ."""
        return pika.URLParameters(self.connection_url)

    def connect(self) -> bool:
        """
        Establish connection to RabbitMQ.
        Returns True if successful, False otherwise.
        """
        if self._is_connected:
            return True

        with self._connection_lock:
            try:
                params = self._get_connection_parameters()
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                self._is_connected = True
                self._reconnect_delay = 0
                logger.info("Successfully connected to RabbitMQ")
                return True
            except AMQPConnectionError as e:
                self._is_connected = False
                self._reconnect_delay = min(30, self._reconnect_delay + 5)
                logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying in {self._reconnect_delay}s")
                time.sleep(self._reconnect_delay)
                return False

    def ensure_connection(self) -> bool:
        """
        Ensure there is an active connection to RabbitMQ.
        Returns True if connected, False otherwise.
        """
        if not self._is_connected or not self.connection or self.connection.is_closed:
            return self.connect()
        return True

    def _setup_exchanges_and_queues(self) -> None:
        """Set up all exchanges and queues defined in config."""
        if not self.ensure_connection():
            logger.error("Cannot set up exchanges and queues without connection")
            return

        try:
            # Set up Dead Letter Exchange (DLX)
            self.channel.exchange_declare(
                exchange=DLX_CONFIG["exchange"],
                exchange_type=DLX_CONFIG["type"],
                durable=DLX_CONFIG["durable"]
            )

            # Set up DLX queue
            self.channel.queue_declare(
                queue=DLX_QUEUE["name"],
                durable=True,
                arguments=DLX_QUEUE["arguments"]
            )

            self.channel.queue_bind(
                queue=DLX_QUEUE["name"],
                exchange=DLX_CONFIG["exchange"],
                routing_key=DLX_QUEUE["routing_key"]
            )

            # Set up main exchanges
            exchanges = set(config["exchange"] for config in QUEUE_CONFIGS.values())
            for exchange in exchanges:
                self.channel.exchange_declare(
                    exchange=exchange,
                    exchange_type="direct",
                    durable=True
                )

            # Set up all queues
            for queue_enum, config in QUEUE_CONFIGS.items():
                queue_name = queue_enum.value
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments=config["arguments"]
                )

                self.channel.queue_bind(
                    queue=queue_name,
                    exchange=config["exchange"],
                    routing_key=config["routing_key"]
                )

            logger.info("Successfully set up all exchanges and queues")
        except (AMQPConnectionError, AMQPChannelError) as e:
            logger.error(f"Failed to set up exchanges and queues: {e}")
            self._is_connected = False

    def publish_message(
        self,
        queue: Queues,
        message: Dict[str, Any],
        priority: int = 0,
        correlation_id: str = None,
    ) -> bool:
        """
        Publish a message to a queue with rate limiting.

        Args:
            queue: Queue enum to publish to
            message: Message body as dictionary
            priority: Message priority (0-9, higher is more priority)
            correlation_id: Optional correlation ID for the message

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ensure_connection():
            return False

        queue_config = QUEUE_CONFIGS.get(queue)
        if not queue_config:
            logger.error(f"Unknown queue: {queue}")
            return False

        # Apply rate limiting if configured
        if queue in RATE_LIMITS:
            now = time.time()
            last_time = self._last_message_time.get(queue, 0)
            min_interval = 1.0 / RATE_LIMITS[queue]

            if now - last_time < min_interval:
                # We're sending too fast, sleep to maintain the rate limit
                sleep_time = min_interval - (now - last_time)
                time.sleep(sleep_time)
                now = time.time()

            self._last_message_time[queue] = now

        try:
            import json
            properties = pika.BasicProperties(
                content_type='application/json',
                delivery_mode=2,  # persistent
                priority=priority,
                correlation_id=correlation_id
            )

            self.channel.basic_publish(
                exchange=queue_config["exchange"],
                routing_key=queue_config["routing_key"],
                body=json.dumps(message),
                properties=properties
            )
            return True
        except (AMQPConnectionError, AMQPChannelError) as e:
            logger.error(f"Failed to publish message to {queue.value}: {e}")
            self._is_connected = False
            return False

    def consume_messages(
        self,
        queue: Queues,
        callback: Callable[[Dict[str, Any], Dict[str, Any]], None],
        prefetch_count: int = 10
    ) -> None:
        """
        Start consuming messages from a queue.

        Args:
            queue: Queue enum to consume from
            callback: Function to call for each message
            prefetch_count: Number of messages to prefetch
        """
        if not self.ensure_connection():
            raise ConnectionError("Not connected to RabbitMQ")

        queue_name = queue.value

        # Set QoS / prefetch count
        self.channel.basic_qos(prefetch_count=prefetch_count)

        def on_message(ch, method, properties, body):
            try:
                import json
                message = json.loads(body)
                message_info = {
                    'routing_key': method.routing_key,
                    'delivery_tag': method.delivery_tag,
                    'correlation_id': properties.correlation_id,
                    'priority': properties.priority,
                    'timestamp': properties.timestamp,
                }

                # Process message
                callback(message, message_info)

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Reject and requeue the message
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )

        logger.info(f"Started consuming from queue {queue_name}")
        try:
            self.channel.start_consuming()
        except (KeyboardInterrupt, SystemExit):
            self.channel.stop_consuming()

    def close(self) -> None:
        """Close the connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            if self.channel and not self.channel.is_closed:
                try:
                    self.channel.close()
                except Exception as e:
                    logger.warning(f"Error closing channel: {e}")

            try:
                self.connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

        self._is_connected = False

    def __del__(self):
        """Clean up resources when this object is garbage collected."""
        self.close()

# Create a singleton instance
queue_manager = QueueManager()

# Helper functions for common operations
def publish_to_queue(queue: Queues, message: Dict[str, Any], priority: int = 0, correlation_id: str = None) -> bool:
    """
    Publish a message to a queue.

    Args:
        queue: Queue enum to publish to
        message: Message body
        priority: Message priority (0-9)
        correlation_id: Optional correlation ID
    """
    return queue_manager.publish_message(queue, message, priority, correlation_id)

def setup_consumer(queue: Queues, callback: Callable, prefetch_count: int = 10) -> threading.Thread:
    """
    Set up a consumer for a queue in a separate thread.

    Args:
        queue: Queue enum to consume from
        callback: Function to call for each message
        prefetch_count: Number of messages to prefetch

    Returns:
        Thread object for the consumer
    """
    def consumer_thread():
        # Create a new connection for this thread
        thread_manager = QueueManager()
        try:
            thread_manager.consume_messages(queue, callback, prefetch_count)
        except Exception as e:
            logger.error(f"Consumer thread error: {e}")
        finally:
            thread_manager.close()

    thread = threading.Thread(target=consumer_thread, daemon=True)
    thread.start()
    return thread
