"""
Campaign models for the Maily platform.

This module contains the shared campaign models used across the Maily platform.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class CampaignType(str, Enum):
    """Campaign type enumeration."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SOCIAL = "social"
    MULTICHANNEL = "multichannel"


@dataclass
class CampaignContent:
    """Campaign content data."""
    subject: str
    preheader: Optional[str] = None
    body: Optional[str] = None
    html: Optional[str] = None
    template_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)


@dataclass
class CampaignMetrics:
    """Campaign performance metrics."""
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    unsubscribed: int = 0
    bounced: int = 0
    complaints: int = 0
    revenue: float = 0
    conversion_rate: float = 0
    last_updated: Optional[datetime] = None


@dataclass
class Campaign:
    """Campaign model."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    type: CampaignType = CampaignType.EMAIL
    content: CampaignContent = field(default_factory=CampaignContent)
    segment_id: Optional[str] = None
    metrics: CampaignMetrics = field(default_factory=CampaignMetrics)
    schedule_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert campaign to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, CampaignStatus) else self.status,
            "type": self.type.value if isinstance(self.type, CampaignType) else self.type,
            "content": {
                "subject": self.content.subject,
                "preheader": self.content.preheader,
                "body": self.content.body,
                "html": self.content.html,
                "template_id": self.content.template_id,
                "variables": self.content.variables,
                "attachments": self.content.attachments,
            },
            "segment_id": self.segment_id,
            "metrics": {
                "sent": self.metrics.sent,
                "delivered": self.metrics.delivered,
                "opened": self.metrics.opened,
                "clicked": self.metrics.clicked,
                "unsubscribed": self.metrics.unsubscribed,
                "bounced": self.metrics.bounced,
                "complaints": self.metrics.complaints,
                "revenue": self.metrics.revenue,
                "conversion_rate": self.metrics.conversion_rate,
                "last_updated": self.metrics.last_updated.isoformat() if self.metrics.last_updated else None,
            },
            "schedule_time": self.schedule_time.isoformat() if self.schedule_time else None,
            "sent_time": self.sent_time.isoformat() if self.sent_time else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        """Create campaign from dictionary."""
        content_data = data.get("content", {})
        metrics_data = data.get("metrics", {})
        
        # Parse datetime fields
        schedule_time = None
        if data.get("schedule_time"):
            schedule_time = datetime.fromisoformat(data["schedule_time"])
        
        sent_time = None
        if data.get("sent_time"):
            sent_time = datetime.fromisoformat(data["sent_time"])
        
        created_at = datetime.utcnow()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = datetime.utcnow()
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        metrics_last_updated = None
        if metrics_data.get("last_updated"):
            metrics_last_updated = datetime.fromisoformat(metrics_data["last_updated"])
        
        # Create content object
        content = CampaignContent(
            subject=content_data.get("subject", ""),
            preheader=content_data.get("preheader"),
            body=content_data.get("body"),
            html=content_data.get("html"),
            template_id=content_data.get("template_id"),
            variables=content_data.get("variables", {}),
            attachments=content_data.get("attachments", []),
        )
        
        # Create metrics object
        metrics = CampaignMetrics(
            sent=metrics_data.get("sent", 0),
            delivered=metrics_data.get("delivered", 0),
            opened=metrics_data.get("opened", 0),
            clicked=metrics_data.get("clicked", 0),
            unsubscribed=metrics_data.get("unsubscribed", 0),
            bounced=metrics_data.get("bounced", 0),
            complaints=metrics_data.get("complaints", 0),
            revenue=metrics_data.get("revenue", 0),
            conversion_rate=metrics_data.get("conversion_rate", 0),
            last_updated=metrics_last_updated,
        )
        
        # Create campaign object
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description"),
            status=CampaignStatus(data["status"]) if data.get("status") else CampaignStatus.DRAFT,
            type=CampaignType(data["type"]) if data.get("type") else CampaignType.EMAIL,
            content=content,
            segment_id=data.get("segment_id"),
            metrics=metrics,
            schedule_time=schedule_time,
            sent_time=sent_time,
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )