# ==============================================================================
# frontend/Dockerfile - Next.js 15 Web Application Container
# ==============================================================================
# Stage 1: Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install npm dependencies
RUN npm ci

# Copy source files
COPY . .

# Set production environment variable for build time
ENV NEXT_PUBLIC_API_URL=http://localhost:8050/api/v1

# Build production bundle
RUN npm run build

# Stage 2: Production runner stage
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

# Copy node_modules and built assets from builder
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-p", "3000"]
