# -------- Stage 1: Build Angular app --------
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Ensure this output path matches your angular.json configuration
RUN npm run build -- --configuration production --output-path=dist/kalakaari-shop/browser

# -------- Stage 2: Serve with Nginx --------
FROM nginx:alpine
# Ensure this source path matches the build output path above
COPY --from=build /app/dist/kalakaari-shop/browser /usr/share/nginx/html
# Ensure nginx.conf is in the same directory as this Dockerfile
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Expose the port Nginx will listen on (matching cloudrun.yaml and nginx.conf)
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]