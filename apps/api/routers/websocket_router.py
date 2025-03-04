"""
WebSocket router for real-time data streaming.
Provides endpoints for analytics, recommendation, and event streaming.
"""
from typing import Dict, Any, List, Optional
import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import structlog

from ..cache.redis_pubsub import RedisPubSub, get_redis_pubsub
from ..services.predictive_analytics_service import PredictiveAnalyticsService, get_predictive_analytics_service
from ..logging.logging_config import bind_contextvars
from ..monitoring.metrics import record_metric

logger = structlog.get_logger("justmaily.api.websocket")

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active connections
active_connections: Dict[str, WebSocket] = {}

# Store client subscriptions
client_subscriptions: Dict[str, Dict[str, Any]] = {}


async def get_analytics_data(client_id: str, subscription: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate analytics data for the client based on their subscription.
    
    Args:
        client_id: Client identifier
        subscription: Subscription details
        
    Returns:
        Analytics data payload
    """
    # Get subscription details
    user_id = subscription.get("userId")
    campaign_id = subscription.get("campaignId")
    metrics = subscription.get("metrics", ["opens", "clicks", "conversions"])
    
    # Generate mock data for development
    # In production, this would fetch real data from database/cache
    metrics_data = []
    for i, metric_name in enumerate(["Active Sessions", "Engagement Rate", "Conversion Rate", "Response Time"]):
        # Add some randomness to make it look real-time
        random_change = (random.random() - 0.5) * 8
        
        if metric_name == "Active Sessions":
            value = random.randint(140, 180)
            unit = ""
        elif metric_name == "Engagement Rate":
            value = round(random.uniform(2.8, 4.5), 1)
            unit = "%"
        elif metric_name == "Conversion Rate":
            value = round(random.uniform(1.8, 3.0), 1)
            unit = "%"
        else:  # Response Time
            value = random.randint(220, 350)
            unit = "ms"
        
        # Previous value logic
        previous_value = value * (1 - random_change/100)
        
        # Trend direction
        trend = "up" if random_change > 0 else "down" if random_change < 0 else "stable"
        
        metrics_data.append({
            "id": str(i + 1),
            "name": metric_name,
            "value": value,
            "previousValue": previous_value,
            "unit": unit,
            "change": round(random_change, 1),
            "trend": trend,
            "timestamp": datetime.now().isoformat()
        })
    
    return {
        "type": "metrics",
        "clientId": client_id,
        "metrics": metrics_data,
        "timestamp": datetime.now().isoformat()
    }


async def get_active_users() -> Dict[str, Any]:
    """
    Get count of active users.
    
    Returns:
        Active users count payload
    """
    return {
        "type": "users",
        "count": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }


async def generate_events(client_id: str, subscription: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate events data for the client.
    
    Args:
        client_id: Client identifier
        subscription: Subscription details
        
    Returns:
        Event data payload
    """
    # Event types that could be generated
    event_types = [
        "Campaign Interaction",
        "Recommendation Applied",
        "Subject Line Optimized",
        "Email Opened",
        "Link Clicked",
        "Subscriber Activity",
        "Unsubscribe Event",
        "Bounce Detected"
    ]
    
    # Messages for each event type
    event_messages = {
        "Campaign Interaction": [
            "User clicked on promotional link in email campaign #1245",
            "User opened welcome email from campaign #1187",
            "New signup from campaign landing page"
        ],
        "Recommendation Applied": [
            "Subject line optimization recommendation applied to campaign #1245",
            "Send time optimization applied to newsletter campaign",
            "Content personalization recommendation implemented for segment 'Active Users'"
        ],
        "Subject Line Optimized": [
            "AI-suggested subject line activated for campaign #985",
            "A/B test automated winner selection completed for campaign #1122",
            "Emoji optimization applied to subject lines for higher engagement"
        ],
        "Email Opened": [
            "Welcome email opened by new subscriber",
            "Follow-up email opened by high-value customer",
            "Re-engagement campaign email opened by inactive user"
        ],
        "Link Clicked": [
            "Product recommendation link clicked in newsletter",
            "Call-to-action button clicked in promotional email",
            "Survey link clicked in feedback request email"
        ],
        "Subscriber Activity": [
            "New subscriber joined mailing list from landing page",
            "User updated subscription preferences",
            "Subscriber moved to 'engaged' segment based on activity"
        ],
        "Unsubscribe Event": [
            "User unsubscribed from promotional emails",
            "User downgraded from daily to weekly digest",
            "Subscription paused for 30 days by user"
        ],
        "Bounce Detected": [
            "Hard bounce detected for email address",
            "Repeated soft bounces - address flagged for review",
            "Delivery issue detected for domain - rate limiting applied"
        ]
    }
    
    # Randomly select event type and message
    event_type = random.choice(event_types)
    event_message = random.choice(event_messages[event_type])
    
    # Determine priority based on event type
    priority_map = {
        "Campaign Interaction": "medium",
        "Recommendation Applied": "high",
        "Subject Line Optimized": "medium",
        "Email Opened": "low",
        "Link Clicked": "medium",
        "Subscriber Activity": "low",
        "Unsubscribe Event": "high",
        "Bounce Detected": "high"
    }
    
    return {
        "type": "event",
        "clientId": client_id,
        "event": {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "message": event_message,
            "timestamp": datetime.now().isoformat(),
            "priority": priority_map[event_type]
        },
        "timestamp": datetime.now().isoformat()
    }


@router.websocket("/analytics")
async def websocket_analytics_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    pubsub: RedisPubSub = Depends(get_redis_pubsub),
    analytics_service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service)
):
    """
    WebSocket endpoint for real-time analytics data.
    
    Args:
        websocket: WebSocket connection
        client_id: Optional client ID for reconnection
        pubsub: Redis PubSub client
        analytics_service: Predictive analytics service
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = f"client_{uuid.uuid4()}"
    
    await websocket.accept()
    
    # Store connection
    active_connections[client_id] = websocket
    
    # Set default subscription
    client_subscriptions[client_id] = {
        "userId": None,
        "campaignId": None,
        "metrics": ["opens", "clicks", "conversions"]
    }
    
    logger.info(
        "WebSocket client connected",
        client_id=client_id,
        active_connections=len(active_connections)
    )
    
    # Record connection metric
    record_metric(
        "websocket.connection.active",
        len(active_connections),
        {"connection_type": "analytics"}
    )
    
    try:
        # Send initial active users count
        await websocket.send_text(json.dumps(await get_active_users()))
        
        # Send initial analytics data
        initial_data = await get_analytics_data(client_id, client_subscriptions[client_id])
        await websocket.send_text(json.dumps(initial_data))
        
        # Start background task for periodic updates
        background_task = asyncio.create_task(send_periodic_updates(websocket, client_id))
        
        # Listen for client messages
        while True:
            data = await websocket.receive_text()
            await process_client_message(websocket, client_id, data, pubsub)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected", client_id=client_id)
        
        # Clean up
        if client_id in active_connections:
            del active_connections[client_id]
        
        if client_id in client_subscriptions:
            del client_subscriptions[client_id]
        
        # Record connection metric
        record_metric(
            "websocket.connection.active",
            len(active_connections),
            {"connection_type": "analytics"}
        )
        
    except Exception as e:
        logger.error(
            "WebSocket error",
            client_id=client_id,
            error=str(e)
        )
        
        # Clean up
        if client_id in active_connections:
            del active_connections[client_id]
        
        if client_id in client_subscriptions:
            del client_subscriptions[client_id]
        
        # Record error metric
        record_metric(
            "websocket.error",
            1,
            {
                "connection_type": "analytics",
                "error_type": type(e).__name__
            }
        )


async def process_client_message(
    websocket: WebSocket,
    client_id: str,
    data: str,
    pubsub: RedisPubSub
):
    """
    Process incoming message from client.
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        data: Raw message data
        pubsub: Redis PubSub client
    """
    try:
        message = json.loads(data)
        
        if message.get("type") == "subscribe":
            # Update subscription
            subscription_data = message.get("data", {})
            client_subscriptions[client_id].update(subscription_data)
            
            # Subscribe to relevant Redis channels
            if subscription_data.get("campaignId"):
                campaign_id = subscription_data["campaignId"]
                await pubsub.subscribe(f"campaign:{campaign_id}:events")
            
            # Acknowledge subscription
            await websocket.send_text(json.dumps({
                "type": "subscribed",
                "clientId": client_id,
                "subscription": client_subscriptions[client_id],
                "timestamp": datetime.now().isoformat()
            }))
            
            logger.info(
                "Client subscription updated",
                client_id=client_id,
                subscription=client_subscriptions[client_id]
            )
        
        elif message.get("type") == "ping":
            # Respond to ping
            await websocket.send_text(json.dumps({
                "type": "pong",
                "clientId": client_id,
                "timestamp": datetime.now().isoformat()
            }))
        
        else:
            logger.warning(
                "Unknown message type",
                client_id=client_id,
                message_type=message.get("type")
            )
    
    except json.JSONDecodeError:
        logger.error(
            "Invalid JSON message",
            client_id=client_id,
            data=data[:100]  # Log first 100 chars only
        )
    
    except Exception as e:
        logger.error(
            "Error processing client message",
            client_id=client_id,
            error=str(e)
        )


async def send_periodic_updates(websocket: WebSocket, client_id: str):
    """
    Send periodic updates to the client.
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
    """
    try:
        # Counter for less frequent updates
        counter = 0
        
        while client_id in active_connections:
            # Regular metrics update (every 5 seconds)
            if counter % 5 == 0:
                analytics_data = await get_analytics_data(
                    client_id, 
                    client_subscriptions[client_id]
                )
                await websocket.send_text(json.dumps(analytics_data))
            
            # Active users update (every 10 seconds)
            if counter % 10 == 0:
                active_users_data = await get_active_users()
                await websocket.send_text(json.dumps(active_users_data))
            
            # Random events (20% chance every second)
            if random.random() < 0.2:
                event_data = await generate_events(
                    client_id,
                    client_subscriptions[client_id]
                )
                await websocket.send_text(json.dumps(event_data))
            
            # Increment counter
            counter = (counter + 1) % 60
            
            # Wait before next update
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(
            "Error in periodic updates",
            client_id=client_id,
            error=str(e)
        )