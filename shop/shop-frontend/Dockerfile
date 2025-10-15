# -------- Stage 1: Build Angular app --------
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Install deps first (cached if package.json/package-lock.json unchanged)
COPY package*.json ./
RUN npm ci

# Copy the rest of the source code
COPY . .

# Build Angular app for production
RUN npm run build -- --configuration production --output-path=dist/kalakaari-shop/browser

# -------- Stage 2: Serve with Nginx --------
FROM nginx:alpine

# Copy built Angular app to Nginx HTML dir
COPY --from=build /app/dist/kalakaari-shop/browser /usr/share/nginx/html

# Add custom nginx config (for Angular SPA routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]