"""
Recommendation models for the Maily platform.

This module contains shared recommendation models used across the platform.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class RecommendationType(str, Enum):
    """Recommendation type enumeration."""
    THRESHOLD = "threshold"
    TREND = "trend"
    ANOMALY = "anomaly"
    COMPARISON = "comparison"
    AI_GENERATED = "ai_generated"


class RecommendationAction(str, Enum):
    """User actions on recommendations."""
    VIEW = "view"
    CLICK = "click"
    DISMISS = "dismiss"
    APPLY = "apply"


@dataclass
class RecommendationContext:
    """Context data for a recommendation."""
    metric: str
    value: float
    confidence: float
    threshold: Optional[float] = None
    previousValue: Optional[float] = None
    changePercent: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    """Recommendation model."""
    id: str
    rule_id: str
    rule_name: str
    type: RecommendationType
    message: str
    suggestion: str
    context: RecommendationContext
    priority: int
    tags: List[str] = field(default_factory=list)
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    dismissed: bool = False
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "type": self.type.value if isinstance(self.type, RecommendationType) else self.type,
            "message": self.message,
            "suggestion": self.suggestion,
            "context": {
                "metric": self.context.metric,
                "value": self.context.value,
                "confidence": self.context.confidence,
                "threshold": self.context.threshold,
                "previousValue": self.context.previousValue,
                "changePercent": self.context.changePercent,
                "metadata": self.context.metadata,
            },
            "priority": self.priority,
            "tags": self.tags,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "dismissed": self.dismissed,
            "applied": self.applied,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        """Create recommendation from dictionary."""
        context_data = data.get("context", {})
        
        # Parse datetime fields
        timestamp = datetime.utcnow()
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])
        
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        # Create context object
        context = RecommendationContext(
            metric=context_data.get("metric", ""),
            value=context_data.get("value", 0.0),
            confidence=context_data.get("confidence", 0.0),
            threshold=context_data.get("threshold"),
            previousValue=context_data.get("previousValue"),
            changePercent=context_data.get("changePercent"),
            metadata=context_data.get("metadata", {}),
        )
        
        # Create recommendation object
        return cls(
            id=data["id"],
            rule_id=data["rule_id"],
            rule_name=data["rule_name"],
            type=RecommendationType(data["type"]) if data.get("type") else RecommendationType.THRESHOLD,
            message=data["message"],
            suggestion=data["suggestion"],
            context=context,
            priority=data["priority"],
            tags=data.get("tags", []),
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            user_id=data.get("user_id"),
            timestamp=timestamp,
            expires_at=expires_at,
            dismissed=data.get("dismissed", False),
            applied=data.get("applied", False),
        )


@dataclass
class RecommendationInteraction:
    """Record of a user interaction with a recommendation."""
    id: str
    recommendation_id: str
    user_id: str
    action: RecommendationAction
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary."""
        return {
            "id": self.id,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "action": self.action.value if isinstance(self.action, RecommendationAction) else self.action,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecommendationInteraction":
        """Create interaction from dictionary."""
        # Parse datetime fields
        timestamp = datetime.utcnow()
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])
        
        # Create interaction object
        return cls(
            id=data["id"],
            recommendation_id=data["recommendation_id"],
            user_id=data["user_id"],
            action=RecommendationAction(data["action"]) if data.get("action") else RecommendationAction.VIEW,
            entity_id=data.get("entity_id"),
            entity_type=data.get("entity_type"),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )