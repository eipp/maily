#!/usr/bin/env python3
import glob
import os
import shutil
from pathlib import Path

import psycopg2
import redis
from loguru import logger

from ..config import settings


def clean_logs():
    """Clean log files."""
    try:
        log_dir = Path("logs")
        if log_dir.exists():
            # Remove all log files except the current one
            current_log = f"maily_{logger._now().strftime('%Y-%m-%d')}.log"
            for log_file in log_dir.glob("maily_*.log"):
                if log_file.name != current_log:
                    log_file.unlink()
            logger.info("Log files cleaned successfully")
    except Exception as e:
        logger.error(f"Failed to clean log files: {e}")


def clean_cache():
    """Clean Redis cache."""
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        # Clear all keys with prefix 'campaign:'
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="campaign:*")
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break
        logger.info("Redis cache cleaned successfully")
    except Exception as e:
        logger.error(f"Failed to clean Redis cache: {e}")


def clean_temp_files():
    """Clean temporary files."""
    try:
        # Clean __pycache__ directories
        for cache_dir in glob.glob("**/__pycache__", recursive=True):
            shutil.rmtree(cache_dir)

        # Clean .pyc files
        for pyc_file in glob.glob("**/*.pyc", recursive=True):
            os.remove(pyc_file)

        # Clean .pyo files
        for pyo_file in glob.glob("**/*.pyo", recursive=True):
            os.remove(pyo_file)

        # Clean .pyd files
        for pyd_file in glob.glob("**/*.pyd", recursive=True):
            os.remove(pyd_file)

        # Clean .pytest_cache
        pytest_cache = Path(".pytest_cache")
        if pytest_cache.exists():
            shutil.rmtree(pytest_cache)

        # Clean .coverage files
        coverage_file = Path(".coverage")
        if coverage_file.exists():
            coverage_file.unlink()

        logger.info("Temporary files cleaned successfully")
    except Exception as e:
        logger.error(f"Failed to clean temporary files: {e}")


def clean_db_temp():
    """Clean temporary database records."""
    try:
        conn = psycopg2.connect(
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )
        cur = conn.cursor()

        # Clean old campaign results (older than 30 days)
        cur.execute(
            """
            DELETE FROM campaigns
            WHERE created_at < NOW() - INTERVAL '30 days'
            AND status IN ('completed', 'failed')
        """
        )

        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database temporary records cleaned successfully")
    except Exception as e:
        logger.error(f"Failed to clean database temporary records: {e}")


def main():
    """Main cleanup function."""
    logger.info("Starting cleanup process...")

    clean_logs()
    clean_cache()
    clean_temp_files()
    clean_db_temp()

    logger.info("Cleanup process completed")


if __name__ == "__main__":
    main()
