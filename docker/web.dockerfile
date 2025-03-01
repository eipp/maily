FROM node:18-alpine as build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of the code
COPY apps/web ./apps/web
COPY packages ./packages
COPY tsconfig.json ./

# Build the Next.js application
RUN npm run build:web

# Production image
FROM node:18-alpine

WORKDIR /app

# Copy built assets from the build stage
COPY --from=build /app/apps/web/.next ./.next
COPY --from=build /app/apps/web/public ./public
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

# Set environment variables
ENV NODE_ENV production
ENV PORT 3000

# Expose the application port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "start:web"]