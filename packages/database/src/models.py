from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """User model for the database."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    consents = relationship("ConsentRecord", back_populates="user")
    user_configs = relationship("UserConfig", back_populates="user")
    campaigns = relationship("Campaign", back_populates="user")
    templates = relationship("EmailTemplate", back_populates="user")


class UserConfig(Base):
    """User configuration model."""
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_configs")


class Campaign(Base):
    """Campaign model for the database."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task = Column(Text, nullable=False)
    status = Column(String, default="pending", nullable=False)
    result = Column(JSON)
    metadata = Column(JSON)
    subject = Column(String)
    body = Column(Text)
    image_url = Column(String)
    analytics_data = Column(JSON)
    personalization_data = Column(JSON)
    delivery_data = Column(JSON)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    template = relationship("EmailTemplate", back_populates="campaigns")


class EmailTemplate(Base):
    """Email template model for saving and reusing email designs."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    content = Column(JSON, nullable=False)  # Stores the fabric.js canvas JSON
    thumbnail = Column(String)  # URL to template thumbnail
    category = Column(String)
    tags = Column(JSON)  # Array of tags
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="templates")
    campaigns = relationship("Campaign", back_populates="template")


class ConsentRecord(Base):
    """Consent record model for GDPR compliance."""
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    marketing_emails = Column(Boolean, default=False)
    data_analytics = Column(Boolean, default=False)
    third_party_sharing = Column(Boolean, default=False)
    personalization = Column(Boolean, default=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="consents")


class Plugin(Base):
    """Plugin registration model."""
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    version = Column(String, nullable=False)
    description = Column(Text)
    author = Column(String)
    website = Column(String)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings = relationship("PluginSetting", back_populates="plugin", cascade="all, delete-orphan")


class PluginSetting(Base):
    """Plugin settings model."""
    __tablename__ = "plugin_settings"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for global settings
    settings = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plugin = relationship("Plugin", back_populates="settings")
    user = relationship("User")
