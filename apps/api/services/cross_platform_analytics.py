"""Cross-platform analytics service."""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum

from ..config.settings import get_settings
from ..utils.redis_utils import get_redis_client
from ..services.platform_service import PlatformService

logger = logging.getLogger(__name__)
settings = get_settings()

class AnalyticsMetricType(str, Enum):
    """Types of analytics metrics."""
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    CONVERSION_RATE = "conversion_rate"
    UNSUBSCRIBE_RATE = "unsubscribe_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    DELIVERY_RATE = "delivery_rate"
    BOUNCE_RATE = "bounce_rate"


class AnalyticsTimeFrame(str, Enum):
    """Time frames for analytics data."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


class AnalyticsPlatform(str, Enum):
    """Supported platforms for analytics."""
    EMAIL = "email"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    ALL = "all"


class CrossPlatformAnalytics:
    """Service for cross-platform analytics aggregation and analysis."""

    def __init__(self):
        """Initialize the analytics service."""
        self.redis = None
        self.platform_service = PlatformService()

    async def get_redis(self):
        """Get Redis client, creating if necessary."""
        if not self.redis:
            self.redis = await get_redis_client()
        return self.redis

    async def track_event(
        self,
        event_type: str,
        user_id: str,
        campaign_id: str,
        platform: AnalyticsPlatform,
        properties: Dict[str, Any]
    ) -> str:
        """Track an analytics event.

        Args:
            event_type: Type of event
            user_id: User ID
            campaign_id: Campaign ID
            platform: Platform where event occurred
            properties: Event properties

        Returns:
            Event ID
        """
        event_id = f"event_{uuid.uuid4().hex}"
        timestamp = datetime.utcnow().isoformat()

        event_data = {
            "id": event_id,
            "type": event_type,
            "user_id": user_id,
            "campaign_id": campaign_id,
            "platform": platform,
            "properties": properties,
            "timestamp": timestamp
        }

        # Store in Redis
        redis = await self.get_redis()
        await redis.set(f"event:{event_id}", json.dumps(event_data))

        # Add to time-series indexes
        day_key = f"events:{campaign_id}:{platform}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        await redis.sadd(day_key, event_id)
        await redis.expire(day_key, 60 * 60 * 24 * 30)  # 30 days

        # Add to campaign index
        campaign_key = f"campaign:{campaign_id}:events"
        await redis.sadd(campaign_key, event_id)

        logger.info(f"Tracked event {event_id} for user {user_id} on {platform}")
        return event_id

    async def get_campaign_metrics(
        self,
        campaign_id: str,
        platforms: Optional[List[AnalyticsPlatform]] = None,
        timeframe: AnalyticsTimeFrame = AnalyticsTimeFrame.DAY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get metrics for a campaign across platforms.

        Args:
            campaign_id: Campaign ID
            platforms: Platforms to include (None for all)
            timeframe: Time frame for metrics
            start_date: Start date for custom timeframe
            end_date: End date for custom timeframe

        Returns:
            Metrics data
        """
        if platforms is None:
            platforms = [p for p in AnalyticsPlatform if p != AnalyticsPlatform.ALL]

        # Calculate date range
        if timeframe == AnalyticsTimeFrame.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom timeframe requires start_date and end_date")
        else:
            end_date = datetime.utcnow()
            if timeframe == AnalyticsTimeFrame.HOUR:
                start_date = end_date - timedelta(hours=1)
            elif timeframe == AnalyticsTimeFrame.DAY:
                start_date = end_date - timedelta(days=1)
            elif timeframe == AnalyticsTimeFrame.WEEK:
                start_date = end_date - timedelta(weeks=1)
            elif timeframe == AnalyticsTimeFrame.MONTH:
                start_date = end_date - timedelta(days=30)
            elif timeframe == AnalyticsTimeFrame.QUARTER:
                start_date = end_date - timedelta(days=90)
            elif timeframe == AnalyticsTimeFrame.YEAR:
                start_date = end_date - timedelta(days=365)
            elif timeframe == AnalyticsTimeFrame.ALL_TIME:
                start_date = datetime(2000, 1, 1)  # Arbitrary past date

        # Get metrics for each platform
        all_metrics = {}
        tasks = []

        for platform in platforms:
            task = asyncio.create_task(
                self._get_platform_metrics(campaign_id, platform, start_date, end_date)
            )
            tasks.append((platform, task))

        # Wait for all tasks to complete
        for platform, task in tasks:
            try:
                platform_metrics = await task
                all_metrics[platform] = platform_metrics
            except Exception as e:
                logger.error(f"Error getting metrics for {platform}: {e}")
                all_metrics[platform] = {"error": str(e)}

        # Calculate aggregate metrics
        aggregate = self._calculate_aggregate_metrics(all_metrics)
        all_metrics[AnalyticsPlatform.ALL] = aggregate

        return {
            "campaign_id": campaign_id,
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics": all_metrics
        }

    async def _get_platform_metrics(
        self,
        campaign_id: str,
        platform: AnalyticsPlatform,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get metrics for a specific platform.

        Args:
            campaign_id: Campaign ID
            platform: Platform to get metrics for
            start_date: Start date
            end_date: End date

        Returns:
            Platform metrics
        """
        # For email platform, use internal data
        if platform == AnalyticsPlatform.EMAIL:
            return await self._get_email_metrics(campaign_id, start_date, end_date)

        # For other platforms, use platform integration service
        return await self.platform_service.get_platform_analytics(
            campaign_id=campaign_id,
            platform=platform,
            start_date=start_date,
            end_date=end_date
        )

    async def _get_email_metrics(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get email metrics from internal data.

        Args:
            campaign_id: Campaign ID
            start_date: Start date
            end_date: End date

        Returns:
            Email metrics
        """
        redis = await self.get_redis()

        # Get events for this campaign in the date range
        event_ids = set()
        current_date = start_date

        while current_date <= end_date:
            day_key = f"events:{campaign_id}:{AnalyticsPlatform.EMAIL}:{current_date.strftime('%Y-%m-%d')}"
            day_events = await redis.smembers(day_key)
            event_ids.update(day_events)
            current_date += timedelta(days=1)

        # Fetch all events
        events = []
        for event_id in event_ids:
            event_data = await redis.get(f"event:{event_id}")
            if event_data:
                events.append(json.loads(event_data))

        # Calculate metrics
        total_sent = 0
        total_delivered = 0
        total_opened = 0
        total_clicked = 0
        total_unsubscribed = 0
        total_bounced = 0

        for event in events:
            event_type = event.get("type")

            if event_type == "email_sent":
                total_sent += 1
            elif event_type == "email_delivered":
                total_delivered += 1
            elif event_type == "email_opened":
                total_opened += 1
            elif event_type == "email_clicked":
                total_clicked += 1
            elif event_type == "email_unsubscribed":
                total_unsubscribed += 1
            elif event_type == "email_bounced":
                total_bounced += 1

        # Calculate rates
        metrics = {
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_unsubscribed": total_unsubscribed,
            "total_bounced": total_bounced
        }

        if total_sent > 0:
            metrics["delivery_rate"] = round(total_delivered / total_sent * 100, 2)
            metrics["bounce_rate"] = round(total_bounced / total_sent * 100, 2)

        if total_delivered > 0:
            metrics["open_rate"] = round(total_opened / total_delivered * 100, 2)
            metrics["click_rate"] = round(total_clicked / total_delivered * 100, 2)
            metrics["unsubscribe_rate"] = round(total_unsubscribed / total_delivered * 100, 2)

        if total_opened > 0:
            metrics["click_to_open_rate"] = round(total_clicked / total_opened * 100, 2)

        return metrics

    def _calculate_aggregate_metrics(self, platform_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics across platforms.

        Args:
            platform_metrics: Metrics for each platform

        Returns:
            Aggregate metrics
        """
        aggregate = {
            "engagement_rate": 0,
            "total_engagements": 0,
            "total_reach": 0,
            "platforms_count": len(platform_metrics)
        }

        # Sum up relevant metrics
        for platform, metrics in platform_metrics.items():
            if "error" in metrics:
                continue

            # Add platform-specific metrics with platform prefix
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and not key.endswith("_rate"):
                    aggregate[f"{platform}_{key}"] = value

                    # Add to totals
                    if key == "total_engagements":
                        aggregate["total_engagements"] += value
                    elif key == "total_reach" or key == "total_delivered":
                        aggregate["total_reach"] += value

        # Calculate overall engagement rate
        if aggregate["total_reach"] > 0:
            aggregate["engagement_rate"] = round(
                aggregate["total_engagements"] / aggregate["total_reach"] * 100, 2
            )

        return aggregate

    async def compare_campaigns(
        self,
        campaign_ids: List[str],
        metrics: List[AnalyticsMetricType],
        platform: AnalyticsPlatform = AnalyticsPlatform.ALL
    ) -> Dict[str, Any]:
        """Compare metrics across multiple campaigns.

        Args:
            campaign_ids: List of campaign IDs to compare
            metrics: Metrics to compare
            platform: Platform to compare on

        Returns:
            Comparison data
        """
        # Get metrics for each campaign
        all_campaign_metrics = {}
        for campaign_id in campaign_ids:
            campaign_data = await self.get_campaign_metrics(
                campaign_id=campaign_id,
                platforms=[platform] if platform != AnalyticsPlatform.ALL else None,
                timeframe=AnalyticsTimeFrame.ALL_TIME
            )
            all_campaign_metrics[campaign_id] = campaign_data

        # Extract comparison metrics
        comparison = {metric: {} for metric in metrics}
        for campaign_id, campaign_data in all_campaign_metrics.items():
            platform_metrics = campaign_data["metrics"][platform]

            for metric in metrics:
                metric_value = platform_metrics.get(metric.value, 0)
                comparison[metric][campaign_id] = metric_value

        return {
            "comparison": comparison,
            "campaigns": campaign_ids,
            "platform": platform,
            "metrics": metrics
        }

    async def get_real_time_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get real-time stats for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Real-time stats
        """
        # Get events from the last hour
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Get metrics for the last hour
        metrics = await self.get_campaign_metrics(
            campaign_id=campaign_id,
            timeframe=AnalyticsTimeFrame.HOUR
        )

        # Add timestamps for time-series data
        time_series = {}

        # 5-minute buckets for the last hour
        for i in range(12):
            bucket_time = hour_ago + timedelta(minutes=i*5)
            bucket_key = bucket_time.strftime("%H:%M")
            time_series[bucket_key] = {
                "emails_opened": 0,
                "emails_clicked": 0,
                "social_engagements": 0
            }

        # Calculate active users
        active_users = set()

        # Get email events
        email_metrics = metrics["metrics"].get(AnalyticsPlatform.EMAIL, {})

        # Get social metrics
        social_platforms = [p for p in AnalyticsPlatform if p not in [AnalyticsPlatform.EMAIL, AnalyticsPlatform.ALL]]
        social_metrics = {}

        for platform in social_platforms:
            if platform in metrics["metrics"]:
                social_metrics[platform] = metrics["metrics"][platform]

        return {
            "campaign_id": campaign_id,
            "timestamp": now.isoformat(),
            "last_hour": {
                "email": email_metrics,
                "social": social_metrics
            },
            "time_series": time_series,
            "active_users": len(active_users)
        }
