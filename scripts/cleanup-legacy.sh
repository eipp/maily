#!/bin/bash

set -euo pipefail

echo "Starting repository cleanup..."

# Remove empty script stubs
echo "Removing empty script stubs..."
rm -f scripts/{ops,validate,backup,rollback,monitor,deploy}.sh

# Remove temporary and cache files
echo "Removing temporary and cache files..."
find . -type f -name "*.tmp" -delete
find . -type f -name "*.swp" -delete
find . -type f -name "*.bak" -delete
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type f -name ".DS_Store" -delete

# Clean build artifacts
echo "Cleaning build artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".coverage" -exec rm -rf {} +
find . -type d -name "htmlcov" -exec rm -rf {} +
find . -type d -name ".tox" -exec rm -rf {} +

# Remove duplicate deployment script from root if it matches scripts/deploy.sh
if cmp -s "deploy.sh" "scripts/deploy.sh" 2>/dev/null; then
    echo "Removing duplicate deploy.sh from root..."
    rm -f deploy.sh
fi

# Clean old logs
echo "Cleaning old logs..."
find ./logs -type f -name "*.log" -mtime +30 -delete 2>/dev/null || true

# Report results
echo "Cleanup complete!"
echo "Run git status to review changes before committing" 