#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Initializing Vault for development environment...${NC}"

# Ensure Vault is running
if ! docker-compose ps | grep -q vault; then
  echo -e "${RED}Vault service is not running. Please start it with 'docker-compose up -d vault'${NC}"
  exit 1
fi

# Wait for Vault to be ready
echo -e "${YELLOW}Waiting for Vault to be ready...${NC}"
until docker-compose exec vault vault status > /dev/null 2>&1; do
  echo -n "."
  sleep 1
done
echo -e "${GREEN}Vault is ready!${NC}"

# Enable KV secrets engine
echo -e "${YELLOW}Enabling KV secrets engine...${NC}"
docker-compose exec vault vault secrets enable -path=secret kv-v2
echo -e "${GREEN}KV secrets engine enabled!${NC}"

# Generate random passwords
echo -e "${YELLOW}Generating secure random passwords...${NC}"
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Store database credentials
echo -e "${YELLOW}Storing database credentials in Vault...${NC}"
docker-compose exec vault vault kv put secret/database \
  username=postgres \
  password=$DB_PASSWORD \
  host=db \
  port=5432 \
  dbname=maily

# Store Redis credentials
echo -e "${YELLOW}Storing Redis credentials in Vault...${NC}"
docker-compose exec vault vault kv put secret/redis \
  host=redis \
  port=6379 \
  password=$REDIS_PASSWORD

# Update PostgreSQL password
echo -e "${YELLOW}Updating PostgreSQL password...${NC}"
docker-compose exec db psql -U postgres -c "ALTER USER postgres WITH PASSWORD '$DB_PASSWORD';"

# Update Redis password
echo -e "${YELLOW}Updating Redis password (requires Redis restart)...${NC}"
docker-compose exec redis redis-cli CONFIG SET requirepass "$REDIS_PASSWORD"
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" CONFIG REWRITE

echo -e "${GREEN}Vault has been initialized with secrets!${NC}"
echo -e "${YELLOW}Please restart the API and workers services to use the new credentials:${NC}"
echo -e "${YELLOW}  docker-compose restart api workers${NC}"
