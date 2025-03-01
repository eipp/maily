#!/bin/bash

# Standardize Dockerfiles
#
# This script standardizes Dockerfiles across the Maily project:
# 1. Creates standardized Dockerfiles for each service
# 2. Adds consistent patterns and best practices
# 3. Removes duplicate Dockerfiles
# 4. Updates docker-compose.yml to use the standardized Dockerfiles

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create backup directory
BACKUP_DIR="${PROJECT_ROOT}/dockerfile_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}Standardizing Dockerfiles...${NC}"
echo -e "${YELLOW}Backup directory: ${BACKUP_DIR}${NC}"

# Backup existing Dockerfiles
backup_file() {
  local file="$1"
  local relative_path="${file#$PROJECT_ROOT/}"
  local backup_path="${BACKUP_DIR}/${relative_path}"

  mkdir -p "$(dirname "$backup_path")"
  cp "$file" "$backup_path"
  echo "Backed up $relative_path"
}

# Find all Dockerfiles
find_dockerfiles() {
  find "$PROJECT_ROOT" -name "Dockerfile*" -not -path "*/node_modules/*" -not -path "*/.git/*"
}

# Backup all Dockerfiles
for dockerfile in $(find_dockerfiles); do
  backup_file "$dockerfile"
done

# Create standardized API Dockerfile
cat > "${PROJECT_ROOT}/apps/api/Dockerfile" << 'EOF'
# Maily API Dockerfile
# Standardized for production use

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 maily && \
    adduser --system --uid 1001 --gid 1001 maily && \
    chown -R maily:maily /app

# Switch to non-root user
USER maily

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "Created standardized API Dockerfile"

# Create standardized Web Dockerfile
cat > "${PROJECT_ROOT}/apps/web/Dockerfile" << 'EOF'
# Maily Web Dockerfile
# Standardized for production use

FROM node:18-alpine AS deps

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED=1

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

# Set working directory
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs --ingroup nodejs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose the port the app runs on
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/api/health || exit 1

# Command to run the application
CMD ["node", "server.js"]
EOF

echo "Created standardized Web Dockerfile"

# Create standardized Workers Dockerfile
cat > "${PROJECT_ROOT}/apps/workers/Dockerfile" << 'EOF'
# Maily Workers Dockerfile
# Standardized for production use

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 maily && \
    adduser --system --uid 1001 --gid 1001 maily && \
    chown -R maily:maily /app

# Switch to non-root user
USER maily

# Command to run the worker
CMD ["python", "-m", "workers.email_worker"]
EOF

echo "Created standardized Workers Dockerfile"

# Create documentation
cat > "${PROJECT_ROOT}/DOCKER.md" << 'EOF'
# Maily Docker Standardization

This document outlines the standardization of Docker configurations for the Maily project.

## Dockerfile Locations

The project uses standardized Dockerfiles for each service:

| Service | Dockerfile Location |
|---------|---------------------|
| API | `apps/api/Dockerfile` |
| Web | `apps/web/Dockerfile` |
| Workers | `apps/workers/Dockerfile` |

## Docker Best Practices

All Dockerfiles follow these best practices:

1. **Multi-stage builds** for optimized image size
2. **Non-root users** for improved security
3. **Health checks** for better container monitoring
4. **Proper caching** of dependencies
5. **Minimal base images** to reduce attack surface
6. **Clear documentation** with comments

## API Dockerfile

The API Dockerfile:
- Uses Python 3.11 slim image
- Installs only necessary system dependencies
- Sets appropriate Python environment variables
- Creates a non-root user for security
- Includes a health check endpoint

## Web Dockerfile

The Web Dockerfile:
- Uses a multi-stage build process
- Separates dependency installation, build, and runtime stages
- Optimizes for Next.js applications
- Creates a non-root user for security
- Includes a health check endpoint

## Workers Dockerfile

The Workers Dockerfile:
- Uses Python 3.11 slim image
- Sets appropriate environment variables
- Creates a non-root user for security
- Configures for background processing

## Docker Compose

The docker-compose.yml file has been updated to use the standardized Dockerfiles.

## Building Images

To build the Docker images:

```bash
# Build API image
docker build -t maily-api:latest -f apps/api/Dockerfile .

# Build Web image
docker build -t maily-web:latest -f apps/web/Dockerfile .

# Build Workers image
docker build -t maily-workers:latest -f apps/workers/Dockerfile .
```

## Running Containers

To run the containers using docker-compose:

```bash
docker-compose up
```
EOF

echo "Created Docker documentation"

# Update docker-compose.yml
backup_file "${PROJECT_ROOT}/docker-compose.yml"

cat > "${PROJECT_ROOT}/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/maily
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./apps/api:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    volumes:
      - ./apps/web:/app
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  workers:
    build:
      context: ./apps/workers
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/maily
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./apps/workers:/app

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=maily
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
EOF

echo "Updated docker-compose.yml"

# Remove duplicate Dockerfiles
for dockerfile in $(find "$PROJECT_ROOT/infrastructure/docker" -name "Dockerfile*"); do
  echo "Removing duplicate Dockerfile: $dockerfile"
  rm "$dockerfile"
done

echo -e "${GREEN}Dockerfile standardization complete!${NC}"
echo -e "${YELLOW}Backup created at: ${BACKUP_DIR}${NC}"
echo "Please review the generated files and make any necessary adjustments."
