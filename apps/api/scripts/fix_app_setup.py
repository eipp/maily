#!/usr/bin/env python3
"""
Setup fix script that resolves common configuration and setup issues
in the Maily application.
"""
import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Create necessary directories
def create_missing_directories():
    """Create missing directories needed by the application."""
    print("\n===== Creating Missing Directories =====")
    dirs_to_create = [
        'database',
        'cache',
        'models',
        'monitoring',
        'config',
        'static'
    ]

    for dir_name in dirs_to_create:
        dir_path = os.path.join(parent_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        else:
            print(f"ℹ️ Directory already exists: {dir_path}")

# Create essential missing files
def create_essential_files():
    """Create essential missing files needed by the application."""
    print("\n===== Creating Essential Files =====")

    # Create database/session.py
    session_path = os.path.join(parent_dir, 'database', 'session.py')
    if not os.path.exists(session_path):
        with open(session_path, 'w') as f:
            f.write("""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Fix the DATABASE_URL format to remove schema parameter
db_url = os.getenv("DATABASE_URL")
if db_url and "schema" in db_url:
    # Remove schema parameter from connection string
    db_url = db_url.split("?")[0]

# Create engine with modified URL
engine = create_engine(
    db_url or "postgresql://postgres:postgres@localhost:5432/maily"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""")
        print(f"✅ Created file: {session_path}")
    else:
        print(f"ℹ️ File already exists: {session_path}")

    # Create cache/redis_client.py
    redis_client_path = os.path.join(parent_dir, 'cache', 'redis_client.py')
    if not os.path.exists(redis_client_path):
        with open(redis_client_path, 'w') as f:
            f.write("""
import os
import redis
from loguru import logger

# Parse REDIS_URL if available, otherwise use default localhost
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    redis_url = "redis://localhost:6379/0"

try:
    # Connect to Redis using URL
    redis_client = redis.from_url(redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
    logger.info(f"Redis client initialized successfully using {redis_url}")
except Exception as e:
    logger.error(f"Failed to initialize Redis: {e}")
    redis_client = None
""")
        print(f"✅ Created file: {redis_client_path}")
    else:
        print(f"ℹ️ File already exists: {redis_client_path}")

    # Create models/campaign.py
    campaign_model_path = os.path.join(parent_dir, 'models', 'campaign.py')
    if not os.path.exists(campaign_model_path):
        with open(campaign_model_path, 'w') as f:
            f.write("""
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.session import Base

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    ERROR = "error"

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_configs.user_id"))
    task = Column(Text, nullable=False)
    status = Column(String, default=CampaignStatus.DRAFT)
    result = Column(JSON)
    metadata = Column(JSON)
    subject = Column(Text)
    body = Column(Text)
    image_url = Column(String)
    analytics_data = Column(JSON)
    personalization_data = Column(JSON)
    delivery_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
""")
        print(f"✅ Created file: {campaign_model_path}")
    else:
        print(f"ℹ️ File already exists: {campaign_model_path}")

    # Create config file for settings
    settings_path = os.path.join(parent_dir, 'config', 'settings.py')
    if not os.path.exists(settings_path):
        with open(settings_path, 'w') as f:
            f.write("""
import os
from functools import lru_cache

class Settings:
    APP_NAME = "Maily API"
    APP_DESCRIPTION = "AI-driven email marketing platform API"
    APP_VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    API_KEY = os.getenv("API_KEY", "test-api-key")
    PREVIEW_URL = os.getenv("PREVIEW_URL", "http://localhost:3000/preview")

@lru_cache()
def get_settings():
    return Settings()
""")
        print(f"✅ Created file: {settings_path}")
    else:
        print(f"ℹ️ File already exists: {settings_path}")

# Create a proper .env file
def create_env_file():
    """Create a proper .env file with the correct settings."""
    print("\n===== Creating Environment File =====")

    env_path = os.path.join(parent_dir, '.env')
    if os.path.exists(env_path):
        backup_path = env_path + '.backup'
        shutil.copy2(env_path, backup_path)
        print(f"ℹ️ Backed up existing .env file to {backup_path}")


    with open(env_path, 'w') as f:
        f.write("""
# Maily Environment Variables for Local Development

# Database Configuration (fixed format)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/maily

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_URL=http://localhost:8000/api
APP_URL=http://localhost:3000
PORT=8000
ENVIRONMENT=development

# Authentication
JWT_SECRET=local-development-jwt-secret-key
JWT_EXPIRATION=86400
API_KEY=test-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
""")
    print(f"✅ Created new .env file: {env_path}")

# Adapt the Docker settings for local development
def adapt_docker_for_local():
    """Create a docker-compose.override.yml for local development."""
    print("\n===== Creating Docker Override =====")

    override_path = os.path.join(os.path.dirname(parent_dir), 'docker-compose.override.yml')
    with open(override_path, 'w') as f:
        f.write("""
version: '3.8'

services:
  api:
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@localhost:5432/maily
      - REDIS_URL=redis://localhost:6379/0
      - ENVIRONMENT=development
    network_mode: "host"

  web:
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://localhost:8000
    network_mode: "host"

  workers:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@localhost:5432/maily
      - REDIS_URL=redis://localhost:6379/0
    network_mode: "host"

  db:
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=maily

  redis:
    ports:
      - "6379:6379"
""")
    print(f"✅ Created docker override file: {override_path}")

# Fix import paths in campaign_service.py
def fix_campaign_service():
    """Fix import paths in campaign_service.py."""
    print("\n===== Fixing Import Paths =====")

    # Create backend directory and symlinks
    backend_dir = os.path.join(parent_dir, 'backend')
    if not os.path.exists(backend_dir):
        os.makedirs(backend_dir, exist_ok=True)

        # Create subdirectories
        os.makedirs(os.path.join(backend_dir, 'models'), exist_ok=True)
        os.makedirs(os.path.join(backend_dir, 'config'), exist_ok=True)
        os.makedirs(os.path.join(backend_dir, 'utils'), exist_ok=True)

        print(f"✅ Created backend directory structure: {backend_dir}")

    # Create symlink for campaign model
    campaign_link = os.path.join(backend_dir, 'models', 'campaign.py')
    campaign_target = os.path.join(parent_dir, 'models', 'campaign.py')
    if os.path.exists(campaign_target) and not os.path.exists(campaign_link):
        os.symlink(campaign_target, campaign_link)
        print(f"✅ Created symlink for campaign model")

    # Create queue_config.py
    queue_config_path = os.path.join(backend_dir, 'config', 'queue_config.py')
    if not os.path.exists(queue_config_path):
        with open(queue_config_path, 'w') as f:
            f.write("""
from enum import Enum

class Queues(str, Enum):
    CAMPAIGN_PROCESSING = "campaign_processing"
    CAMPAIGN_SCHEDULING = "campaign_scheduling"
    EMAIL_HIGH_PRIORITY = "email_high_priority"
    EMAIL_REGULAR = "email_regular"
    EMAIL_BULK = "email_bulk"
""")
        print(f"✅ Created queue_config.py")

    # Create queue_manager.py
    queue_manager_path = os.path.join(backend_dir, 'utils', 'queue_manager.py')
    if not os.path.exists(queue_manager_path):
        with open(queue_manager_path, 'w') as f:
            f.write("""
from loguru import logger

def publish_to_queue(queue, message, priority=0, correlation_id=None):
    """
    Publish a message to a queue.
    This is a stub function for local development.

    Args:
        queue: Queue name
        message: Message to publish
        priority: Message priority
        correlation_id: Correlation ID

    Returns:
        bool: True if published, False otherwise
    """
    logger.info(f"Would publish to queue {queue.value} with priority {priority}")
    logger.debug(f"Message: {message}")
    return True
""")
        print(f"✅ Created queue_manager.py")

# Create database initialization script
def create_db_init_script():
    """Create a script to initialize the database."""
    print("\n===== Creating Database Init Script =====")

    init_script_path = os.path.join(parent_dir, 'scripts', 'init_db.py')
    if not os.path.exists(os.path.dirname(init_script_path)):
        os.makedirs(os.path.dirname(init_script_path), exist_ok=True)

    with open(init_script_path, 'w') as f:
        f.write("""#!/usr/bin/env python3
import os
import sys
import psycopg2

# Add parent directory to path to allow imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from database.migrations import initialize_schema

def main():
    """Initialize the database with the required schema."""
    print("Initializing database schema...")

    try:
        # Run schema initialization
        initialize_schema()
        print("Database schema initialized successfully!")
    except Exception as e:
        print(f"Error initializing database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
""")
    os.chmod(init_script_path, 0o755)
    print(f"✅ Created database init script: {init_script_path}")

# Main function
def main():
    print("======================================================")
    print("  Maily App Setup Fix")
    print("  Resolving common configuration and setup issues")
    print("======================================================")

    create_missing_directories()
    create_essential_files()
    create_env_file()
    adapt_docker_for_local()
    fix_campaign_service()
    create_db_init_script()

    print("\n======================================================")
    print("  Setup fix completed!")
    print("  Next steps:")
    print("  1. Start PostgreSQL locally (or using Docker)")
    print("  2. Run: python scripts/init_db.py")
    print("  3. Start the app: uvicorn main:app --reload")
    print("======================================================")

if __name__ == "__main__":
    main()
