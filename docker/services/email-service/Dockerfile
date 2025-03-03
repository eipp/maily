FROM node:20.11.1-alpine

WORKDIR /app

# Install dependencies
COPY apps/email-service/package*.json ./
RUN npm ci --only=production

# Copy application code
COPY apps/email-service ./

# Set environment variables
ENV NODE_ENV=production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -u 1001 -G nodejs nodejs
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:8081/health || exit 1

# Expose port
EXPOSE 8081

# Run the application
CMD ["node", "src/index.js"]

# Metadata
LABEL org.opencontainers.image.title="Maily Email Service"
LABEL org.opencontainers.image.description="Email delivery and processing service for Maily"
LABEL org.opencontainers.image.vendor="Maily Inc."
LABEL org.opencontainers.image.source="https://github.com/yourusername/maily"
LABEL org.opencontainers.image.version="1.0.0"