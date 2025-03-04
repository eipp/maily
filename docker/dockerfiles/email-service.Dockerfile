# Multi-stage build for Email Service
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies
COPY apps/email-service/package.json apps/email-service/package-lock.json ./
RUN npm ci

# Runtime stage
FROM node:20-alpine

WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY apps/email-service .

# Set environment variables
ENV NODE_ENV production

# Run as non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 appuser
USER appuser

# Expose port
EXPOSE 3001

# Command to run the application
CMD ["node", "src/index.js"]
