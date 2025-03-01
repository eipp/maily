"""
Analytics Worker Module.

This worker handles analytics processing, including tracking events,
aggregation of metrics, and generation of reports on a schedule.
"""
import json
import logging
import os
import signal
import sys
import time
import threading
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

import pika
import schedule
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import backend modules - adjust the path as needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config.queue_config import Queues
from backend.utils.queue_manager import QueueManager, setup_consumer
from backend.models.campaign import Campaign, CampaignStatus
from backend.models.email import Email, EmailStatus
from backend.models.tracking import TrackingEvent, EventType

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
AGGREGATION_INTERVAL = int(os.environ.get("AGGREGATION_INTERVAL", "15"))  # minutes
HOURLY_ROLLUP_HOUR = int(os.environ.get("HOURLY_ROLLUP_HOUR", "1"))  # 1 AM
DAILY_ROLLUP_HOUR = int(os.environ.get("DAILY_ROLLUP_HOUR", "2"))  # 2 AM
WEEKLY_ROLLUP_DAY = int(os.environ.get("WEEKLY_ROLLUP_DAY", "1"))  # Monday (0=Sunday)
WEEKLY_ROLLUP_HOUR = int(os.environ.get("WEEKLY_ROLLUP_HOUR", "3"))  # 3 AM
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "90"))  # 90 days

# Create database connection
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Global state for tracking
running = True

def get_db() -> Session:
    """Get a database session."""
    db = Session()
    try:
        yield db
    finally:
        db.close()

class ReportType(Enum):
    """Enum for different report types."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class AnalyticsWorker:
    """Worker for processing analytics data and generating reports."""

    def __init__(self):
        """Initialize the analytics worker."""
        self.queue_manager = QueueManager(RABBITMQ_URL)
        self.consumer_threads = []
        self.scheduler_thread = None
        self.running = True

    def start(self):
        """Start the worker."""
        logger.info("Starting Analytics Worker")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            # Start consumer for tracking events
            self._start_tracking_consumer()

            # Start consumer for report generation requests
            self._start_reporting_consumer()

            # Set up scheduled tasks
            self._setup_scheduled_tasks()

            # Keep the main thread alive
            while running:
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error in analytics worker: {e}")
            self._shutdown()
        finally:
            self._shutdown()

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        global running
        logger.info(f"Received signal {signum}, shutting down")
        running = False
        self.running = False

    def _shutdown(self):
        """Shutdown the worker."""
        logger.info("Shutting down Analytics Worker")
        global running
        running = False
        self.running = False

        # Close queue manager connection
        self.queue_manager.close()

        logger.info("Analytics Worker shut down successfully")

    def _start_tracking_consumer(self):
        """Start consumer for tracking events."""
        tracking_thread = setup_consumer(
            queue=Queues.ANALYTICS_TRACKING,
            callback=self._handle_tracking_event,
            prefetch_count=50  # Higher prefetch for tracking events
        )
        self.consumer_threads.append(tracking_thread)
        logger.info("Started tracking events consumer")

    def _start_reporting_consumer(self):
        """Start consumer for report generation requests."""
        reporting_thread = setup_consumer(
            queue=Queues.ANALYTICS_REPORTING,
            callback=self._handle_reporting_request,
            prefetch_count=5
        )
        self.consumer_threads.append(reporting_thread)
        logger.info("Started reporting requests consumer")

    def _setup_scheduled_tasks(self):
        """Set up scheduled tasks for analytics aggregation."""
        # Real-time aggregation every X minutes
        schedule.every(AGGREGATION_INTERVAL).minutes.do(self._run_realtime_aggregation)

        # Hourly rollups at specific hour
        schedule.every().hour.at(f":{HOURLY_ROLLUP_HOUR}").do(self._run_hourly_rollup)

        # Daily rollups at specific hour
        schedule.every().day.at(f"{DAILY_ROLLUP_HOUR:02d}:00").do(self._run_daily_rollup)

        # Weekly rollups on specific day and hour
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        schedule.every().week.days[days[WEEKLY_ROLLUP_DAY]].at(f"{WEEKLY_ROLLUP_HOUR:02d}:00").do(self._run_weekly_rollup)

        # Data cleanup once a day
        schedule.every().day.at("04:00").do(self._run_data_cleanup)

        # Start the scheduler in a thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Started scheduled tasks")

    def _run_scheduler(self):
        """Run the scheduler in a loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def _handle_tracking_event(self, message: Dict[str, Any], message_info: Dict[str, Any]):
        """
        Handle a tracking event message.

        Args:
            message: Tracking event message
            message_info: Message metadata
        """
        event_type = message.get('event_type')
        message_id = message.get('message_id')
        recipient_id = message.get('recipient_id')
        campaign_id = message.get('campaign_id')
        timestamp = message.get('timestamp', datetime.now().isoformat())
        metadata = message.get('metadata', {})

        try:
            logger.debug(f"Processing tracking event: {event_type} for message {message_id}")

            # Validate message
            if not event_type or not message_id:
                logger.error(f"Invalid tracking event message: missing required fields")
                return

            # Parse timestamp
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)

            # Convert event type to enum
            try:
                event_type_enum = EventType[event_type.upper()]
            except (KeyError, ValueError):
                logger.error(f"Invalid event type: {event_type}")
                return

            # Get database session
            db = next(get_db())
            try:
                # Check if the email exists
                email = db.query(Email).filter(Email.message_id == message_id).first()
                if not email:
                    logger.warning(f"Email with message_id {message_id} not found")
                    # Create tracking event anyway, but without the email ID
                    tracking_event = TrackingEvent(
                        event_type=event_type_enum,
                        message_id=message_id,
                        recipient_id=recipient_id,
                        campaign_id=campaign_id,
                        timestamp=timestamp,
                        metadata=metadata
                    )
                else:
                    # Create tracking event with the email ID
                    tracking_event = TrackingEvent(
                        event_type=event_type_enum,
                        email_id=email.id,
                        message_id=message_id,
                        recipient_id=recipient_id or email.recipient_id,
                        campaign_id=campaign_id or email.campaign_id,
                        timestamp=timestamp,
                        metadata=metadata
                    )

                    # Update email status based on event type
                    if event_type_enum == EventType.OPEN and not email.opened_at:
                        email.opened_at = timestamp
                    elif event_type_enum == EventType.CLICK and not email.clicked_at:
                        email.clicked_at = timestamp
                    elif event_type_enum == EventType.BOUNCE:
                        email.status = EmailStatus.BOUNCED
                    elif event_type_enum == EventType.SPAM:
                        email.status = EmailStatus.SPAM
                    elif event_type_enum == EventType.UNSUBSCRIBE:
                        email.status = EmailStatus.UNSUBSCRIBED

                # Save to database
                db.add(tracking_event)
                db.commit()

                logger.debug(f"Saved tracking event: {event_type} for message {message_id}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error processing tracking event: {e}")

    def _handle_reporting_request(self, message: Dict[str, Any], message_info: Dict[str, Any]):
        """
        Handle a reporting request.

        Args:
            message: Reporting request message
            message_info: Message metadata
        """
        report_type = message.get('report_type')
        user_id = message.get('user_id')
        campaign_id = message.get('campaign_id')
        start_date = message.get('start_date')
        end_date = message.get('end_date')
        aggregation = message.get('aggregation', 'daily')
        callback_queue = message.get('callback_queue')

        try:
            logger.info(f"Processing reporting request: {report_type} for user {user_id}")

            # Validate message
            if not report_type or not user_id:
                logger.error(f"Invalid reporting request message: missing required fields")
                return

            # Parse dates if they are strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)

            # Generate the report
            report = self._generate_report(
                report_type=report_type,
                user_id=user_id,
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date,
                aggregation=aggregation
            )

            # If a callback queue was specified, send the report there
            if callback_queue:
                self.queue_manager.publish_message(
                    queue=Queues[callback_queue] if callback_queue in Queues.__members__ else Queues.NOTIFICATION_USER,
                    message={
                        'type': 'analytics_report',
                        'report_type': report_type,
                        'user_id': user_id,
                        'campaign_id': campaign_id,
                        'report': report
                    }
                )

            logger.info(f"Completed reporting request: {report_type} for user {user_id}")

        except Exception as e:
            logger.error(f"Error processing reporting request: {e}")

    def _generate_report(
        self,
        report_type: str,
        user_id: int,
        campaign_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        aggregation: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Generate an analytics report.

        Args:
            report_type: Type of report to generate
            user_id: User ID to generate report for
            campaign_id: Optional campaign ID to filter by
            start_date: Optional start date for the report
            end_date: Optional end date for the report
            aggregation: Time aggregation ('hourly', 'daily', 'weekly')

        Returns:
            Report data
        """
        # Set default dates if not specified
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            if report_type == 'daily':
                start_date = end_date - timedelta(days=7)
            elif report_type == 'weekly':
                start_date = end_date - timedelta(weeks=4)
            elif report_type == 'monthly':
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)

        db = next(get_db())
        try:
            # Build the base query
            # This is simplified - in a real implementation, you'd use a proper analytics DB or pre-aggregated tables
            base_query = db.query(Campaign).filter(Campaign.user_id == user_id)

            if campaign_id:
                base_query = base_query.filter(Campaign.id == campaign_id)

            campaigns = base_query.all()

            # Collect campaign IDs
            campaign_ids = [c.id for c in campaigns]

            # If no campaigns found, return empty report
            if not campaign_ids:
                return {
                    'report_type': report_type,
                    'user_id': user_id,
                    'campaign_id': campaign_id,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'aggregation': aggregation,
                    'data': []
                }

            # Get email metrics
            email_metrics = self._get_email_metrics(db, campaign_ids, start_date, end_date)

            # Get tracking events
            tracking_events = self._get_tracking_events(db, campaign_ids, start_date, end_date, aggregation)

            # Combine the data
            report_data = {
                'report_type': report_type,
                'user_id': user_id,
                'campaign_id': campaign_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'aggregation': aggregation,
                'campaigns': [{
                    'id': c.id,
                    'name': c.name,
                    'subject': c.subject,
                    'status': c.status.value,
                    'created_at': c.created_at.isoformat(),
                    'sent_at': c.sent_at.isoformat() if c.sent_at else None,
                    'metrics': email_metrics.get(c.id, {})
                } for c in campaigns],
                'events': tracking_events
            }

            return report_data

        finally:
            db.close()

    def _get_email_metrics(
        self,
        db: Session,
        campaign_ids: List[int],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get email metrics for campaigns.

        Args:
            db: Database session
            campaign_ids: List of campaign IDs
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dictionary mapping campaign IDs to metrics
        """
        # Query for sent and delivered counts
        sent_counts = db.query(
            Email.campaign_id,
            func.count().label('sent_count')
        ).filter(
            Email.campaign_id.in_(campaign_ids),
            Email.sent_at >= start_date,
            Email.sent_at <= end_date
        ).group_by(Email.campaign_id).all()

        # Query for opened counts
        opened_counts = db.query(
            Email.campaign_id,
            func.count().label('opened_count')
        ).filter(
            Email.campaign_id.in_(campaign_ids),
            Email.opened_at.is_not(None),
            Email.opened_at >= start_date,
            Email.opened_at <= end_date
        ).group_by(Email.campaign_id).all()

        # Query for clicked counts
        clicked_counts = db.query(
            Email.campaign_id,
            func.count().label('clicked_count')
        ).filter(
            Email.campaign_id.in_(campaign_ids),
            Email.clicked_at.is_not(None),
            Email.clicked_at >= start_date,
            Email.clicked_at <= end_date
        ).group_by(Email.campaign_id).all()

        # Query for bounced, spam, and unsubscribed counts
        bounced_counts = db.query(
            Email.campaign_id,
            func.count().label('bounced_count')
        ).filter(
            Email.campaign_id.in_(campaign_ids),
            Email.status == EmailStatus.BOUNCED,
            Email.sent_at >= start_date,
            Email.sent_at <= end_date
        ).group_by(Email.campaign_id).all()

        spam_counts = db.query(
            Email.campaign_id,
            func.count().label('spam_count')
        ).filter(
            Email.campaign_id.in_(campaign_ids),
            Email.status == EmailStatus.SPAM,
            Email.sent_at >= start_date,
            Email.sent_at <= end_date
        ).group_by(Email.campaign_id).all()

        unsubscribed_counts = db.query(
            Email.campaign_id,
            func.count().label('unsubscribed_count')
        ).filter(
            Email.campaign_id.in_(campaign_ids),
            Email.status == EmailStatus.UNSUBSCRIBED,
            Email.sent_at >= start_date,
            Email.sent_at <= end_date
        ).group_by(Email.campaign_id).all()

        # Build the metrics
        metrics = {}
        for campaign_id in campaign_ids:
            metrics[campaign_id] = {
                'sent': 0,
                'opened': 0,
                'clicked': 0,
                'bounced': 0,
                'spam': 0,
                'unsubscribed': 0,
                'open_rate': 0,
                'click_rate': 0,
                'bounce_rate': 0,
                'spam_rate': 0,
                'unsubscribe_rate': 0
            }

        # Update with actual values
        for campaign_id, sent_count in sent_counts:
            metrics[campaign_id]['sent'] = sent_count

        for campaign_id, opened_count in opened_counts:
            metrics[campaign_id]['opened'] = opened_count

        for campaign_id, clicked_count in clicked_counts:
            metrics[campaign_id]['clicked'] = clicked_count

        for campaign_id, bounced_count in bounced_counts:
            metrics[campaign_id]['bounced'] = bounced_count

        for campaign_id, spam_count in spam_counts:
            metrics[campaign_id]['spam'] = spam_count

        for campaign_id, unsubscribed_count in unsubscribed_counts:
            metrics[campaign_id]['unsubscribed'] = unsubscribed_count

        # Calculate rates
        for campaign_id, data in metrics.items():
            sent = data['sent']
            if sent > 0:
                data['open_rate'] = round(data['opened'] / sent * 100, 2)
                data['click_rate'] = round(data['clicked'] / sent * 100, 2)
                data['bounce_rate'] = round(data['bounced'] / sent * 100, 2)
                data['spam_rate'] = round(data['spam'] / sent * 100, 2)
                data['unsubscribe_rate'] = round(data['unsubscribed'] / sent * 100, 2)

        return metrics

    def _get_tracking_events(
        self,
        db: Session,
        campaign_ids: List[int],
        start_date: datetime,
        end_date: datetime,
        aggregation: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get tracking events aggregated by time.

        Args:
            db: Database session
            campaign_ids: List of campaign IDs
            start_date: Start date for events
            end_date: End date for events
            aggregation: Time aggregation ('hourly', 'daily', 'weekly')

        Returns:
            List of aggregated events
        """
        # Define the date trunc function based on aggregation
        if aggregation == 'hourly':
            date_trunc = 'hour'
        elif aggregation == 'weekly':
            date_trunc = 'week'
        else:
            date_trunc = 'day'  # Default to daily

        # Build the query using SQL text - this is simplified
        query = text(f"""
            SELECT
                date_trunc('{date_trunc}', timestamp) as period,
                campaign_id,
                event_type,
                COUNT(*) as count
            FROM
                tracking_events
            WHERE
                campaign_id IN :campaign_ids
                AND timestamp >= :start_date
                AND timestamp <= :end_date
            GROUP BY
                period,
                campaign_id,
                event_type
            ORDER BY
                period,
                campaign_id,
                event_type
        """)

        result = db.execute(
            query,
            {
                'campaign_ids': tuple(campaign_ids),
                'start_date': start_date,
                'end_date': end_date
            }
        )

        # Transform the result into a list of dictionaries
        events = []
        for row in result:
            events.append({
                'period': row.period.isoformat(),
                'campaign_id': row.campaign_id,
                'event_type': row.event_type,
                'count': row.count
            })

        return events

    def _run_realtime_aggregation(self):
        """Run real-time aggregation of analytics data."""
        logger.info("Running real-time analytics aggregation")

        # In a real implementation, you'd run SQL to aggregate data into a real-time view
        # For now, just simulate the process
        time.sleep(1)

        logger.info("Real-time analytics aggregation completed")

    def _run_hourly_rollup(self):
        """Run hourly rollup of analytics data."""
        logger.info("Running hourly analytics rollup")

        # In a real implementation, you'd run SQL to roll up data into hourly aggregates
        # For now, just simulate the process
        time.sleep(2)

        logger.info("Hourly analytics rollup completed")

    def _run_daily_rollup(self):
        """Run daily rollup of analytics data."""
        logger.info("Running daily analytics rollup")

        # In a real implementation, you'd run SQL to roll up data into daily aggregates
        # For now, just simulate the process
        time.sleep(3)

        logger.info("Daily analytics rollup completed")

    def _run_weekly_rollup(self):
        """Run weekly rollup of analytics data."""
        logger.info("Running weekly analytics rollup")

        # In a real implementation, you'd run SQL to roll up data into weekly aggregates
        # For now, just simulate the process
        time.sleep(5)

        logger.info("Weekly analytics rollup completed")

    def _run_data_cleanup(self):
        """Clean up old data."""
        logger.info("Running data cleanup")

        # Get cutoff date
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)

        db = next(get_db())
        try:
            # Delete old tracking events
            db.query(TrackingEvent).filter(TrackingEvent.timestamp < cutoff_date).delete()

            # For a real implementation, you might archive the data instead of deleting it

            db.commit()
            logger.info(f"Deleted tracking events older than {cutoff_date}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up old data: {e}")
        finally:
            db.close()

def main():
    """Main entry point for the worker."""
    worker = AnalyticsWorker()
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Analytics worker interrupted, shutting down")

if __name__ == "__main__":
    main()
