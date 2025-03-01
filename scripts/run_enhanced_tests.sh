#!/bin/bash
# Script to run tests for the production-enhanced components

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Running Maily Production Quality Tests${NC}"
echo -e "${GREEN}======================================${NC}"

# Setup virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo -e "${YELLOW}Setting up virtual environment...${NC}"
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  pip install pytest pytest-asyncio pytest-cov
else
  source venv/bin/activate
fi

# Run AI adapter tests
echo -e "${YELLOW}Running AI adapter tests...${NC}"
python -m pytest apps/api/tests/ai/test_adapters.py -v

# Run security middleware tests
echo -e "${YELLOW}Running security middleware tests...${NC}"
python -m pytest apps/api/tests/middleware/test_security_headers.py -v

# Run with coverage
echo -e "${YELLOW}Running tests with coverage...${NC}"
python -m pytest --cov=apps.api.ai.adapters --cov=apps.api.middleware --cov=apps.api.errors apps/api/tests/ai apps/api/tests/middleware --cov-report term-missing

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Production Quality Test Suite Complete${NC}"
echo -e "${GREEN}======================================${NC}"
