#!/usr/bin/env python3
"""
Diagnostic script to check database and Redis connections.
Run this script directly to diagnose connection issues.
"""
import os
import sys
import time
import psycopg2
import redis
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check and print relevant environment variables."""
    print("\n===== Environment Variables =====")
    db_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "[set but masked]") if os.getenv("POSTGRES_PASSWORD") else None,
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT"),
    }

    redis_vars = {
        "REDIS_URL": os.getenv("REDIS_URL"),
        "REDIS_HOST": os.getenv("REDIS_HOST"),
        "REDIS_PORT": os.getenv("REDIS_PORT"),
        "REDIS_DB": os.getenv("REDIS_DB"),
        "REDIS_PASSWORD": "[set but masked]" if os.getenv("REDIS_PASSWORD") else None,
    }

    print("\nDatabase Environment Variables:")
    for key, value in db_vars.items():
        print(f"  {key}: {value}")

    print("\nRedis Environment Variables:")
    for key, value in redis_vars.items():
        print(f"  {key}: {value}")

    # Check for conflicts
    if db_vars["DATABASE_URL"] and any([db_vars["POSTGRES_USER"], db_vars["POSTGRES_DB"],
                                       db_vars["POSTGRES_HOST"], db_vars["POSTGRES_PORT"]]):
        print("\n⚠️ WARNING: Both DATABASE_URL and individual Postgres params are set. This may cause conflicts.")

    if redis_vars["REDIS_URL"] and any([redis_vars["REDIS_HOST"], redis_vars["REDIS_PORT"],
                                       redis_vars["REDIS_DB"]]):
        print("\n⚠️ WARNING: Both REDIS_URL and individual Redis params are set. This may cause conflicts.")

def check_postgres_connection():
    """Check the Postgres database connection."""
    print("\n===== Database Connection Test =====")

    # Try connection using DATABASE_URL if available
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"\nTrying to connect using DATABASE_URL...")
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✅ Success! Connected to: {version[0]}")
            conn.close()
        except Exception as e:
            print(f"❌ Error connecting using DATABASE_URL: {e}")

    # Try connection using individual parameters
    user = os.getenv("POSTGRES_USER", "ivanpeychev")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB", "maily")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "6432")

    print(f"\nTrying to connect using individual parameters...")
    print(f"  Host: {host}, Port: {port}, DB: {db}, User: {user}")

    try:
        conn = psycopg2.connect(
            dbname=db,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Success! Connected to: {version[0]}")

        # Check if migrations table exists
        try:
            cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='migration_history');")
            has_migrations_table = cur.fetchone()[0]
            if has_migrations_table:
                print("✅ Migrations table exists. Checking applied migrations...")
                cur.execute("SELECT COUNT(*) FROM migration_history;")
                migration_count = cur.fetchone()[0]
                print(f"  Found {migration_count} applied migrations")
            else:
                print("❌ Migrations table does not exist!")
        except Exception as e:
            print(f"❌ Error checking migrations: {e}")

        conn.close()
    except Exception as e:
        print(f"❌ Error connecting using individual parameters: {e}")

    # Try with docker-compose parameters
    print(f"\nTrying to connect using docker-compose parameters...")
    try:
        conn = psycopg2.connect(
            dbname="maily",
            user="postgres",
            password="postgres",
            host="db",
            port="5432"
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Success! Connected to: {version[0]}")
        conn.close()
    except Exception as e:
        print(f"❌ Error connecting using docker-compose parameters: {e}")

def check_redis_connection():
    """Check the Redis connection."""
    print("\n===== Redis Connection Test =====")

    # Try connection using REDIS_URL if available
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print(f"\nTrying to connect using REDIS_URL: {redis_url}")
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            ping_response = client.ping()
            print(f"✅ Success! Ping response: {ping_response}")
        except Exception as e:
            print(f"❌ Error connecting using REDIS_URL: {e}")

    # Try connection using individual parameters
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    password = os.getenv("REDIS_PASSWORD")

    print(f"\nTrying to connect using individual parameters...")
    print(f"  Host: {host}, Port: {port}, DB: {db}")

    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        ping_response = client.ping()
        print(f"✅ Success! Ping response: {ping_response}")
    except Exception as e:
        print(f"❌ Error connecting using individual parameters: {e}")

    # Try with docker-compose parameters
    print(f"\nTrying to connect using docker-compose parameters...")
    try:
        client = redis.Redis(
            host="redis",
            port=6379,
            db=0,
            decode_responses=True,
        )
        ping_response = client.ping()
        print(f"✅ Success! Ping response: {ping_response}")
    except Exception as e:
        print(f"❌ Error connecting using docker-compose parameters: {e}")

def check_import_paths():
    """Check if critical import paths exist."""
    print("\n===== Import Path Test =====")

    # Check if database/session.py exists
    session_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'session.py')
    print(f"\nChecking for database/session.py: {'exists' if os.path.exists(session_path) else 'does not exist'}")

    # Check if cache/redis_client.py exists
    redis_client_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'redis_client.py')
    print(f"Checking for cache/redis_client.py: {'exists' if os.path.exists(redis_client_path) else 'does not exist'}")

    # Check for models expected by campaign_service.py
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'campaign.py')
    print(f"Checking for models/campaign.py: {'exists' if os.path.exists(model_path) else 'does not exist'}")

    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    print(f"Checking for backend directory: {'exists' if os.path.exists(backend_path) else 'does not exist'}")

if __name__ == "__main__":
    print("======================================================")
    print("  Maily App Diagnostics Tool")
    print("  Checking connections and critical configurations")
    print("======================================================")

    start_time = time.time()

    try:
        check_env_vars()
        check_postgres_connection()
        check_redis_connection()
        check_import_paths()
    except Exception as e:
        print(f"\n❌ Diagnostic tool encountered an error: {e}")

    print("\n======================================================")
    print(f"  Diagnostics completed in {time.time() - start_time:.2f} seconds")
    print("======================================================")
