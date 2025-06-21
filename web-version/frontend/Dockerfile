# Multi-stage build for React frontend
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Development stage
FROM node:18-alpine as development
WORKDIR /app
# Copy package files
COPY package*.json ./
# Install all dependencies (including dev)
RUN npm ci
# Copy source code
COPY . .
# Expose port
EXPOSE 3000
# Development command
CMD ["npm", "start"]

# Build stage
FROM base as build
# Copy source code
COPY . .
# Install all dependencies for build
RUN npm ci
# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine as production
# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html
# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Expose port
EXPOSE 80
# Start nginx
CMD ["nginx", "-g", "daemon off;"]