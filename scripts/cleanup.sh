#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/.."

echo "Starting cleanup process..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Python cleanup script
python -c "from backend.scripts.cleanup import main; main()"

# Additional cleanup commands
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type d -name ".pytest_cache" -exec rm -r {} +
find . -type f -name ".coverage" -delete
find . -type f -name "*.log" ! -name "maily_$(date +%Y-%m-%d).log" -delete

# Clean Docker artifacts if Docker is installed
if command -v docker &> /dev/null; then
    echo "Cleaning Docker artifacts..."
    docker system prune -f
fi

echo "Cleanup completed successfully!"
