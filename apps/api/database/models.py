from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, Float
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
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    model_configs = relationship("ModelConfig", back_populates="user")


class ApiKey(Base):
    """API key model for storing API keys in the database."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    hashed_key = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        """Return string representation of the API key."""
        return f"<ApiKey(id={self.id}, name={self.name}, user_id={self.user_id})>"


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


class ModelConfig(Base):
    """Model configuration for AI models."""
    __tablename__ = "model_configs"

    id = Column(String, primary_key=True)  # Using a string ID for better readability
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for global configurations
    model_name = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    api_key = Column(String, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    parameters = Column(JSON, default={})  # Additional parameters like top_p, frequency_penalty, etc.
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="model_configs")

    def __repr__(self):
        """Return string representation of the model configuration."""
        return f"<ModelConfig(id={self.id}, model_name={self.model_name}, provider={self.provider})>"
