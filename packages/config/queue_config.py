"""
Queue configuration for Maily asynchronous processing.
Defines various queues for different types of tasks with appropriate priorities.
"""
import os
from enum import Enum

# RabbitMQ connection
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# Exchange names
CAMPAIGN_EXCHANGE = "maily.campaign"
EMAIL_EXCHANGE = "maily.email"
ANALYTICS_EXCHANGE = "maily.analytics"
NOTIFICATION_EXCHANGE = "maily.notification"

# Queue names
class Queues(Enum):
    # Campaign queues
    CAMPAIGN_PROCESSING = "campaign.processing"
    CAMPAIGN_SCHEDULING = "campaign.scheduling"

    # Email queues
    EMAIL_SENDING = "email.sending"
    EMAIL_HIGH_PRIORITY = "email.high_priority"
    EMAIL_REGULAR = "email.regular"
    EMAIL_BULK = "email.bulk"

    # Analytics queues
    ANALYTICS_TRACKING = "analytics.tracking"
    ANALYTICS_AGGREGATION = "analytics.aggregation"
    ANALYTICS_REPORTING = "analytics.reporting"

    # Notification queues
    NOTIFICATION_USER = "notification.user"
    NOTIFICATION_ADMIN = "notification.admin"
    NOTIFICATION_SYSTEM = "notification.system"

# Queue configurations with priorities and TTL
QUEUE_CONFIGS = {
    Queues.CAMPAIGN_PROCESSING: {
        "exchange": CAMPAIGN_EXCHANGE,
        "routing_key": "campaign.processing",
        "arguments": {
            "x-message-ttl": 3600000,  # 1 hour
            "x-max-priority": 10,
            "x-max-length": 10000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "campaign.processing.dlx"
        }
    },
    Queues.CAMPAIGN_SCHEDULING: {
        "exchange": CAMPAIGN_EXCHANGE,
        "routing_key": "campaign.scheduling",
        "arguments": {
            "x-message-ttl": 86400000,  # 24 hours
            "x-max-priority": 5,
            "x-max-length": 5000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "campaign.scheduling.dlx"
        }
    },
    Queues.EMAIL_SENDING: {
        "exchange": EMAIL_EXCHANGE,
        "routing_key": "email.sending",
        "arguments": {
            "x-message-ttl": 3600000,  # 1 hour
            "x-max-priority": 10,
            "x-max-length": 100000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "email.sending.dlx"
        }
    },
    Queues.EMAIL_HIGH_PRIORITY: {
        "exchange": EMAIL_EXCHANGE,
        "routing_key": "email.high_priority",
        "arguments": {
            "x-message-ttl": 1800000,  # 30 minutes
            "x-max-priority": 10,
            "x-max-length": 10000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "email.high_priority.dlx"
        }
    },
    Queues.EMAIL_REGULAR: {
        "exchange": EMAIL_EXCHANGE,
        "routing_key": "email.regular",
        "arguments": {
            "x-message-ttl": 3600000,  # 1 hour
            "x-max-priority": 5,
            "x-max-length": 50000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "email.regular.dlx"
        }
    },
    Queues.EMAIL_BULK: {
        "exchange": EMAIL_EXCHANGE,
        "routing_key": "email.bulk",
        "arguments": {
            "x-message-ttl": 86400000,  # 24 hours
            "x-max-priority": 1,
            "x-max-length": 1000000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "email.bulk.dlx"
        }
    },
    Queues.ANALYTICS_TRACKING: {
        "exchange": ANALYTICS_EXCHANGE,
        "routing_key": "analytics.tracking",
        "arguments": {
            "x-message-ttl": 7200000,  # 2 hours
            "x-max-priority": 5,
            "x-max-length": 500000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "analytics.tracking.dlx"
        }
    },
    Queues.ANALYTICS_AGGREGATION: {
        "exchange": ANALYTICS_EXCHANGE,
        "routing_key": "analytics.aggregation",
        "arguments": {
            "x-message-ttl": 86400000,  # 24 hours
            "x-max-priority": 3,
            "x-max-length": 10000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "analytics.aggregation.dlx"
        }
    },
    Queues.ANALYTICS_REPORTING: {
        "exchange": ANALYTICS_EXCHANGE,
        "routing_key": "analytics.reporting",
        "arguments": {
            "x-message-ttl": 86400000,  # 24 hours
            "x-max-priority": 2,
            "x-max-length": 5000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "analytics.reporting.dlx"
        }
    },
    Queues.NOTIFICATION_USER: {
        "exchange": NOTIFICATION_EXCHANGE,
        "routing_key": "notification.user",
        "arguments": {
            "x-message-ttl": 86400000,  # 24 hours
            "x-max-priority": 8,
            "x-max-length": 100000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "notification.user.dlx"
        }
    },
    Queues.NOTIFICATION_ADMIN: {
        "exchange": NOTIFICATION_EXCHANGE,
        "routing_key": "notification.admin",
        "arguments": {
            "x-message-ttl": 604800000,  # 7 days
            "x-max-priority": 9,
            "x-max-length": 10000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "notification.admin.dlx"
        }
    },
    Queues.NOTIFICATION_SYSTEM: {
        "exchange": NOTIFICATION_EXCHANGE,
        "routing_key": "notification.system",
        "arguments": {
            "x-message-ttl": 86400000,  # 24 hours
            "x-max-priority": 10,
            "x-max-length": 50000,
            "x-dead-letter-exchange": "maily.dlx",
            "x-dead-letter-routing-key": "notification.system.dlx"
        }
    }
}

# Dead Letter Exchange (DLX) configuration
DLX_CONFIG = {
    "exchange": "maily.dlx",
    "type": "topic",
    "durable": True
}

# DLX queue for handling failed messages
DLX_QUEUE = {
    "name": "maily.failed_messages",
    "routing_key": "#",
    "arguments": {
        "x-message-ttl": 604800000,  # 7 days
        "x-max-length": 100000
    }
}

# Rate limits for different queue types (messages per second)
RATE_LIMITS = {
    Queues.EMAIL_HIGH_PRIORITY: 100,
    Queues.EMAIL_REGULAR: 50,
    Queues.EMAIL_BULK: 20,
    Queues.ANALYTICS_TRACKING: 200,
    Queues.NOTIFICATION_USER: 50,
}
