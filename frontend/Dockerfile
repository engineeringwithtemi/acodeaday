# Stage 1: Build with placeholder values
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Use placeholder values that will be replaced at runtime
ENV VITE_API_URL=__VITE_API_URL_PLACEHOLDER__
ENV VITE_SUPABASE_URL=__VITE_SUPABASE_URL_PLACEHOLDER__
ENV VITE_SUPABASE_KEY=__VITE_SUPABASE_KEY_PLACEHOLDER__

# Build the application
RUN npm run build

# Stage 2: Production
FROM node:22-alpine

WORKDIR /app

# Install bash for entrypoint script
RUN apk add --no-cache bash

# Copy built output from builder
COPY --from=builder /app/.output ./.output

# Copy node_modules for SSR dependencies that aren't fully bundled
# (e.g., Monaco editor which is dynamically imported)
COPY --from=builder /app/node_modules ./node_modules

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["node", ".output/server/index.mjs"]
