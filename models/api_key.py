"""API key model for storing API keys in the database."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from database.base import Base


class ApiKey(Base):
    """API key model for storing API keys in the database."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    hashed_key = Column(String, nullable=False, index=True)
    scopes = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        """Return string representation of the API key."""
        return f"<ApiKey(id={self.id}, name={self.name}, user_id={self.user_id})>"
