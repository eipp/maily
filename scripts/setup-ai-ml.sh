#!/bin/bash

# Setup script for AI & ML components
# This script installs the required dependencies for the AI & ML components

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

# Check if the required environment variables are set
print_yellow "Checking environment variables..."

# Create a .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_yellow "Creating .env file from .env.example..."
    cp .env.example .env
    print_yellow "Please update the .env file with your API keys and other configuration."
fi

# Check for required API keys
required_keys=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "GOOGLE_API_KEY"
    "WANDB_API_KEY"
    "ARIZE_API_KEY"
    "ARIZE_SPACE_KEY"
    "STABILITY_API_KEY"
    "HELICONE_API_KEY"
)

missing_keys=()
for key in "${required_keys[@]}"; do
    if ! grep -q "^$key=" .env || grep -q "^$key=your_" .env; then
        missing_keys+=("$key")
    fi
done

if [ ${#missing_keys[@]} -gt 0 ]; then
    print_yellow "The following environment variables need to be set in the .env file:"
    for key in "${missing_keys[@]}"; do
        echo "  - $key"
    done
fi

# Initialize DVC if it's not already initialized
if [ ! -d ".dvc" ]; then
    print_yellow "Initializing DVC..."
    dvc init

    # Create a models directory if it doesn't exist
    if [ ! -d "models" ]; then
        mkdir -p models
    fi

    print_yellow "DVC initialized. You may want to configure a remote storage for DVC."
    print_yellow "Example: dvc remote add -d myremote s3://mybucket/dvcstore"
fi

# Initialize Weights & Biases if it's not already initialized
if [ -n "$WANDB_API_KEY" ] && [ "$WANDB_API_KEY" != "your_wandb_api_key" ]; then
    print_yellow "Logging in to Weights & Biases..."
    wandb login "$WANDB_API_KEY"
fi

# Create necessary directories
print_yellow "Creating necessary directories..."
mkdir -p apps/api/cache
mkdir -p apps/api/storage/attachments
mkdir -p .cache/litellm

# Set permissions
print_yellow "Setting permissions..."
chmod -R 755 apps/api/cache
chmod -R 755 apps/api/storage
chmod -R 755 .cache/litellm

print_green "AI & ML components setup completed successfully!"
print_yellow "You can now use the AI & ML components in your application."
print_yellow "Make sure to update the .env file with your API keys and other configuration."
