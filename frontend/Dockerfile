# Multi-stage Dockerfile for Nuxt 4 Frontend

# Stage 1: Dependencies
FROM node:20-alpine as deps

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies)
RUN npm ci

# Copy source code
COPY . .

# Build the Nuxt application
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine as runner

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nuxt -u 1001

# Copy built application from builder
COPY --from=builder --chown=nuxt:nodejs /app/.output /app/.output
COPY --from=builder --chown=nuxt:nodejs /app/package*.json /app/

# Switch to non-root user
USER nuxt

# Expose port
EXPOSE 8901

# Set environment variables
ENV HOST=0.0.0.0 \
    PORT=8901 \
    NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8901', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Start the application
CMD ["node", ".output/server/index.mjs"]
