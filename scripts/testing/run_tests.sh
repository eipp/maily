#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🧪 Running all tests..."

# Frontend Tests
echo -e "\n${GREEN}Running Frontend Tests${NC}"
cd app

echo -e "\n📋 Running ESLint..."
npm run lint || exit 1

echo -e "\n🔍 Running Type Checks..."
npm run type-check || exit 1

echo -e "\n🧪 Running Jest Unit Tests..."
npm run test:coverage || exit 1

echo -e "\n🌐 Running E2E Tests..."
npm run cypress:headless || exit 1

# Backend Tests
cd ../backend
echo -e "\n${GREEN}Running Backend Tests${NC}"

echo -e "\n📋 Running Flake8..."
flake8 . || exit 1

echo -e "\n🧪 Running Python Tests..."
pytest tests/ --cov=. --cov-report=html || exit 1

# Run Lighthouse Tests (if on CI or staging/production)
if [ "$CI" = "true" ] || [ "$ENV" = "staging" ] || [ "$ENV" = "production" ]; then
  echo -e "\n${GREEN}Running Lighthouse Tests${NC}"
  cd ../app
  npm run lighthouse
fi

echo -e "\n${GREEN}All tests completed successfully!${NC}"
