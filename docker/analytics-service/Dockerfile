# Multi-stage build for Analytics Service
FROM node:18-alpine AS builder

WORKDIR /app
COPY packages/analytics/package*.json ./
RUN npm ci --only=production

COPY packages/analytics ./
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY packages/analytics/package*.json ./

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Set environment variables
ENV NODE_ENV=production
ENV PORT=4000

# Add Clickhouse and Elasticsearch client libraries
RUN npm install --save clickhouse-client @elastic/elasticsearch

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:$PORT/health || exit 1

EXPOSE 4000
CMD ["node", "dist/main.js"]
