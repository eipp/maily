#!/bin/bash

# Test script for AI & ML components
# This script runs the tests for the AI & ML components

set -e

# Print colored output
print_green() {
    echo -e "\033[0;32m$1\033[0m"
}

print_yellow() {
    echo -e "\033[0;33m$1\033[0m"
}

print_red() {
    echo -e "\033[0;31m$1\033[0m"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_red "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_red "pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Check if virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    print_yellow "virtualenv is not installed. Installing virtualenv..."
    pip3 install virtualenv
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_yellow "Creating virtual environment..."
    virtualenv venv
fi

# Activate the virtual environment
print_yellow "Activating virtual environment..."
source venv/bin/activate

# Install the AI & ML dependencies
print_yellow "Installing AI & ML dependencies..."
pip install -r apps/api/requirements-ai-ml.txt

# Install test dependencies
print_yellow "Installing test dependencies..."
pip install pytest pytest-asyncio pytest-mock pytest-cov

# Run the tests
print_yellow "Running AI & ML component tests..."
cd apps/api
python -m pytest tests/test_ai_ml_components.py -v

# Run the tests with coverage
print_yellow "Running AI & ML component tests with coverage..."
python -m pytest tests/test_ai_ml_components.py --cov=ai --cov-report=term --cov-report=html

print_green "AI & ML component tests completed successfully!"
print_yellow "Coverage report is available in apps/api/htmlcov/index.html"
