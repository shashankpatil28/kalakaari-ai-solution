# ---------- Build stage ----------
FROM node:20-alpine AS build
WORKDIR /app

# Install deps (fast, reproducible)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
# Uses your angular.json -> outputPath: dist/kalakaari-shop with /browser inside
RUN npm run build

# ---------- Runtime stage ----------
FROM nginx:alpine
WORKDIR /usr/share/nginx/html

# Nginx config for Angular SPA + caching + listen 4200
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy Angular build output (note the /browser directory)
COPY --from=build /app/dist/kalakaari-shop/browser ./

# Cloud Run: we’ll configure the service to use port 4200.
# EXPOSE is a no-op in Cloud Run but helps local runs.
EXPOSE 4200

# Keep Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
