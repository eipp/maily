#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/../.."

echo "Starting cleanup process..."

# Determine Python interpreter
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON="venv/bin/python"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    PYTHON=".venv/bin/python"
elif [ -n "$VIRTUAL_ENV" ]; then
    PYTHON="$VIRTUAL_ENV/bin/python"
else
    PYTHON="python3"
fi

echo "Using Python interpreter: $PYTHON"

# Run Python cleanup script
$PYTHON -c "from backend.scripts.cleanup import main; main()"

# Additional cleanup commands
echo "Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

echo "Cleaning test cache..."
find . -type d -name ".pytest_cache" -exec rm -r {} +
find . -type f -name ".coverage" -delete

echo "Cleaning log files..."
find . -type f -name "*.log" ! -name "maily_$(date +%Y-%m-%d).log" -delete

# Clean Docker artifacts if Docker is installed
if command -v docker &> /dev/null; then
    echo "Cleaning Docker artifacts..."
    docker system prune -f
fi

echo "Cleanup completed successfully!"
