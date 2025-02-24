from loguru import logger
from ..services.database import get_db_connection

def initialize_schema():
    """Initialize database schema with required tables."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create tables
        cur.execute("""
            DROP TABLE IF EXISTS campaigns;
            DROP TABLE IF EXISTS user_configs;
            
            CREATE TABLE IF NOT EXISTS user_configs (
                user_id SERIAL PRIMARY KEY,
                model_name TEXT NOT NULL,
                api_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS campaigns (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES user_configs(user_id),
                task TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result JSONB,
                metadata JSONB,
                subject TEXT,
                body TEXT,
                image_url TEXT,
                analytics_data JSONB,
                personalization_data JSONB,
                delivery_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise 