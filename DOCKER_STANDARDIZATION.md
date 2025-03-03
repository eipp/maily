# Docker Standardization

All Dockerfiles have been standardized with the following best practices:

1. **Multi-stage builds** to reduce final image size
2. **Security hardening** including:
   - Non-root users for each service
   - Minimal base images
   - Reduced attack surface
3. **Build optimizations**:
   - Proper layer caching
   - Dependency installation separated from code changes
4. **Standardized naming** in docker/services directory

The unified docker-compose.yml file provides a complete local development environment with:
- API service
- Web front-end
- AI service
- Email service
- Background workers
- Postgres database
- Redis for caching and messaging

## Usage

```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up api

# Rebuild services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

For production deployment, refer to the Kubernetes manifests in the infrastructure directory.
