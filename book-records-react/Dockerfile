# --- Stage 1: Build the React application ---
FROM node:lts-alpine AS build-site
WORKDIR /app
COPY ./package*.json ./
RUN npm ci
COPY .env.local .env.local
COPY . .
RUN npm run build

# --- Stage 2: Serve the static files with Nginx ---
FROM nginx:alpine
# Copy the custom nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy the built React app static files to the Nginx serving directory
COPY --from=build-site /app/dist /usr/share/nginx/html
EXPOSE 8282
CMD ["nginx", "-g", "daemon off;"]
