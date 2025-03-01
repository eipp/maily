#!/usr/bin/env python3
"""
Simple setup fix script that resolves critical issues in the Maily application.
"""
import os
import sys
import shutil
from pathlib import Path

def create_directories():
    """Create missing directories"""
    print("Creating missing directories...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dirs = ['database', 'cache', 'models', 'monitoring', 'config', 'static', 'backend']

    for d in dirs:
        path = os.path.join(base_dir, d)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"Created: {path}")

    backend_dirs = ['models', 'config', 'utils']
    for d in backend_dirs:
        path = os.path.join(base_dir, 'backend', d)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"Created: {path}")

def create_simple_files():
    """Create basic versions of missing critical files"""
    print("Creating basic files...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # database/session.py
    session_file = os.path.join(base_dir, 'database', 'session.py')
    if not os.path.exists(session_file):
        with open(session_file, 'w') as f:
            f.write('import os\n')
            f.write('from sqlalchemy import create_engine\n')
            f.write('from sqlalchemy.ext.declarative import declarative_base\n')
            f.write('from sqlalchemy.orm import sessionmaker\n\n')
            f.write('# Database URL\n')
            f.write('db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")\n')
            f.write('# Remove schema parameter if present\n')
            f.write('if db_url and "schema" in db_url:\n')
            f.write('    db_url = db_url.split("?")[0]\n\n')
            f.write('# Create engine\n')
            f.write('engine = create_engine(db_url)\n\n')
            f.write('SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n')
            f.write('Base = declarative_base()\n\n')
            f.write('def get_db():\n')
            f.write('    """Get a database session"""\n')
            f.write('    db = SessionLocal()\n')
            f.write('    try:\n')
            f.write('        yield db\n')
            f.write('    finally:\n')
            f.write('        db.close()\n')
        print(f"Created: {session_file}")

    # cache/redis_client.py
    redis_file = os.path.join(base_dir, 'cache', 'redis_client.py')
    if not os.path.exists(redis_file):
        with open(redis_file, 'w') as f:
            f.write('import os\n')
            f.write('import redis\n')
            f.write('from loguru import logger\n\n')
            f.write('# Redis URL\n')
            f.write('redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")\n\n')
            f.write('try:\n')
            f.write('    # Connect to Redis\n')
            f.write('    redis_client = redis.from_url(redis_url, decode_responses=True)\n')
            f.write('    redis_client.ping()  # Test connection\n')
            f.write('    logger.info(f"Redis connected: {redis_url}")\n')
            f.write('except Exception as e:\n')
            f.write('    logger.error(f"Redis connection failed: {e}")\n')
            f.write('    redis_client = None\n')
        print(f"Created: {redis_file}")

    # models/campaign.py
    campaign_file = os.path.join(base_dir, 'models', 'campaign.py')
    if not os.path.exists(campaign_file):
        with open(campaign_file, 'w') as f:
            f.write('from enum import Enum\n')
            f.write('from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime\n')
            f.write('from sqlalchemy.sql import func\n')
            f.write('from database.session import Base\n\n')
            f.write('class CampaignStatus(str, Enum):\n')
            f.write('    DRAFT = "draft"\n')
            f.write('    SCHEDULED = "scheduled"\n')
            f.write('    SENDING = "sending"\n')
            f.write('    SENT = "sent"\n')
            f.write('    ERROR = "error"\n\n')
            f.write('class Campaign(Base):\n')
            f.write('    __tablename__ = "campaigns"\n')
            f.write('    \n')
            f.write('    id = Column(Integer, primary_key=True, index=True)\n')
            f.write('    user_id = Column(Integer, ForeignKey("user_configs.user_id"))\n')
            f.write('    task = Column(Text, nullable=False)\n')
            f.write('    status = Column(String, default=CampaignStatus.DRAFT)\n')
            f.write('    result = Column(JSON)\n')
            f.write('    metadata = Column(JSON)\n')
            f.write('    subject = Column(Text)\n')
            f.write('    body = Column(Text)\n')
            f.write('    image_url = Column(String)\n')
            f.write('    analytics_data = Column(JSON)\n')
            f.write('    personalization_data = Column(JSON)\n')
            f.write('    delivery_data = Column(JSON)\n')
            f.write('    created_at = Column(DateTime, default=func.now())\n')
            f.write('    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())\n')
        print(f"Created: {campaign_file}")

    # Create symlink in backend/models
    backend_model_link = os.path.join(base_dir, 'backend', 'models', 'campaign.py')
    if not os.path.exists(backend_model_link) and os.path.exists(campaign_file):
        try:
            os.symlink(campaign_file, backend_model_link)
            print(f"Created symlink: {backend_model_link}")
        except Exception as e:
            print(f"Failed to create symlink: {e}")

    # backend/config/queue_config.py
    queue_file = os.path.join(base_dir, 'backend', 'config', 'queue_config.py')
    if not os.path.exists(queue_file):
        with open(queue_file, 'w') as f:
            f.write('from enum import Enum\n\n')
            f.write('class Queues(str, Enum):\n')
            f.write('    CAMPAIGN_PROCESSING = "campaign_processing"\n')
            f.write('    CAMPAIGN_SCHEDULING = "campaign_scheduling"\n')
            f.write('    EMAIL_HIGH_PRIORITY = "email_high_priority"\n')
            f.write('    EMAIL_REGULAR = "email_regular"\n')
            f.write('    EMAIL_BULK = "email_bulk"\n')
        print(f"Created: {queue_file}")

    # backend/utils/queue_manager.py
    queue_manager_file = os.path.join(base_dir, 'backend', 'utils', 'queue_manager.py')
    if not os.path.exists(queue_manager_file):
        with open(queue_manager_file, 'w') as f:
            f.write('from loguru import logger\n\n')
            f.write('def publish_to_queue(queue, message, priority=0, correlation_id=None):\n')
            f.write('    """Stub function for queue publishing"""\n')
            f.write('    logger.info(f"Publishing to queue {queue.value} with priority {priority}")\n')
            f.write('    logger.debug(f"Message: {message}")\n')
            f.write('    return True\n')
        print(f"Created: {queue_manager_file}")

def create_env_file():
    """Create basic .env file"""
    print("Creating .env file...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_file = os.path.join(base_dir, '.env')

    if os.path.exists(env_file):
        shutil.copy2(env_file, env_file + '.backup')
        print(f"Backed up existing .env file")

    with open(env_file, 'w') as f:
        f.write('# Maily Environment Variables\n\n')
        f.write('# Database\n')
        f.write('DATABASE_URL=postgresql://postgres:postgres@localhost:5432/maily\n\n')
        f.write('# Redis\n')
        f.write('REDIS_URL=redis://localhost:6379/0\n\n')
        f.write('# API\n')
        f.write('API_URL=http://localhost:8000/api\n')
        f.write('APP_URL=http://localhost:3000\n')
        f.write('PORT=8000\n')
        f.write('ENVIRONMENT=development\n\n')
        f.write('# Auth\n')
        f.write('JWT_SECRET=local-dev-secret\n')
        f.write('API_KEY=test-api-key\n\n')
        f.write('# CORS\n')
        f.write('CORS_ORIGINS=http://localhost:3000,http://localhost:8000\n')
    print(f"Created new .env file")

def main():
    print("====== Maily App Fix ======")
    try:
        create_directories()
        create_simple_files()
        create_env_file()
        print("\nFix completed successfully!")
        print("\nNext steps:")
        print("1. Start PostgreSQL: docker-compose up -d db")
        print("2. Start Redis: docker-compose up -d redis")
        print("3. Start the API: cd apps/api && uvicorn main:app --reload")
    except Exception as e:
        print(f"Error during fix: {e}")

if __name__ == "__main__":
    main()
