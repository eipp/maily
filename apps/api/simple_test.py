#!/usr/bin/env python3
"""
Simple test script to verify project functionality
"""
import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test the database connection with SQLAlchemy"""
    try:
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/maily")
        if "schema" in db_url:
            db_url = db_url.split("?")[0]

        logger.info(f"Using SQLAlchemy with connection URL: {db_url}")

        # Create engine
        engine = create_engine(db_url)

        # Test connection
        logger.info("Testing SQLAlchemy connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"SQLAlchemy query result: {result.fetchone()}")

        logger.info("SQLAlchemy connection test successful!")
        return True
    except Exception as e:
        logger.error(f"SQLAlchemy connection error: {e}")
        return False

def test_project_structure():
    """Verify key project files exist"""
    files_to_check = [
        "main.py",
        "requirements.txt",
        "dependencies.py",
        "Dockerfile"
    ]

    missing_files = []
    for file in files_to_check:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        logger.error(f"Missing key project files: {missing_files}")
        return False
    else:
        logger.info("All key project files present")
        return True

def test_environment_variables():
    """Check that required environment variables are set"""
    required_vars = [
        "DATABASE_URL",
        "ENVIRONMENT"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    else:
        logger.info("All required environment variables present")
        return True

def run_all_tests():
    """Run all tests and summarize results"""
    logger.info("Running all tests...")

    results = {
        "Database Connection": test_database_connection(),
        "Project Structure": test_project_structure(),
        "Environment Variables": test_environment_variables()
    }

    # Print summary
    logger.info("\n----- Test Results -----")
    all_passed = True
    for test_name, passed in results.items():
        logger.info(f"{test_name}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False

    if all_passed:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed.")
        return 1

if __name__ == "__main__":
    run_all_tests()
