import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")
# Remove schema parameter if present
if db_url and "schema" in db_url:
    db_url = db_url.split("?")[0]

# Create engine
engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
