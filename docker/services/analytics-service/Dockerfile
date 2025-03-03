FROM node:20.11.1-alpine

WORKDIR /app

# Install dependencies
COPY apps/analytics-service/package*.json ./
RUN npm ci --only=production

# Copy application code
COPY apps/analytics-service ./

# Set environment variables
ENV NODE_ENV=production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -u 1001 -G nodejs nodejs
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["node", "src/index.js"]

# Metadata
LABEL org.opencontainers.image.title="Maily Analytics Service"
LABEL org.opencontainers.image.description="Analytics processing service for Maily"
LABEL org.opencontainers.image.vendor="Maily Inc."
LABEL org.opencontainers.image.source="https://github.com/yourusername/maily"
LABEL org.opencontainers.image.version="1.0.0"