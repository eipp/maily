# Multi-stage build for Blockchain Service
FROM node:18-alpine AS builder

WORKDIR /app
COPY packages/blockchain/package*.json ./
RUN npm ci --only=production

COPY packages/blockchain ./
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY packages/blockchain/package*.json ./

# Install additional Ethereum dependencies
RUN npm install --save web3 ethers ipfs-http-client

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Set environment variables
ENV NODE_ENV=production
ENV PORT=5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:$PORT/health || exit 1

EXPOSE 5000
CMD ["node", "dist/main.js"]
