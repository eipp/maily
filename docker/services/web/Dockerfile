FROM node:20.11.1-alpine AS base
WORKDIR /app

# Install dependencies only when needed
FROM base AS deps
COPY apps/web/package.json apps/web/package-lock.json* ./
COPY packages packages/
COPY package.json package-lock.json* turbo.json ./
RUN npm ci

# Build the application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages ./packages
COPY apps/web ./
COPY turbo.json ./
COPY tsconfig.json ./

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build the Next.js application
RUN npm run build

# Production image
FROM node:20.11.1-alpine AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from the builder stage
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/api/health || exit 1

# Run the application
CMD ["node", "server.js"]

# Metadata
LABEL org.opencontainers.image.title="Maily Web Application"
LABEL org.opencontainers.image.description="Web frontend for Maily"
LABEL org.opencontainers.image.vendor="Maily Inc."
LABEL org.opencontainers.image.source="https://github.com/yourusername/maily"
LABEL org.opencontainers.image.version="1.0.0"