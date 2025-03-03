"""
Content safety models for the AI service.

These models define the structure for content safety checks, results, and actions.
"""

import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ContentSafetyLevel(enum.Enum):
    """Safety level for content."""
    SAFE = "safe"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"

class ContentSafetyAction(enum.Enum):
    """Recommended action for content safety issues."""
    ALLOW = "allow"
    FLAG_FOR_REVIEW = "flag_for_review"
    BLOCK = "block"

class ContentSafetyCategory(BaseModel):
    """Category for content safety issues."""
    name: str
    score: float
    flagged: bool

class ContentSafetyResult(BaseModel):
    """Result of a content safety check."""
    id: str = ""
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    content_hash: str = ""
    safety_level: ContentSafetyLevel
    categories: List[ContentSafetyCategory] = []
    recommended_action: ContentSafetyAction

class ContentSafetyCheck(Base):
    """Database model for content safety checks."""
    __tablename__ = "content_safety_checks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_hash = Column(String(64), index=True)
    content_snippet = Column(Text)
    safety_level = Column(String(20), index=True)
    categories = Column(JSON)
    action_taken = Column(String(20), index=True)
    timestamp = Column(Float, default=lambda: datetime.now().timestamp(), index=True)
    was_filtered = Column(Boolean, default=False)
    filter_reason = Column(String(255), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content_hash": self.content_hash,
            "content_snippet": self.content_snippet,
            "safety_level": self.safety_level,
            "categories": self.categories,
            "action_taken": self.action_taken,
            "timestamp": self.timestamp,
            "was_filtered": self.was_filtered,
            "filter_reason": self.filter_reason,
        }