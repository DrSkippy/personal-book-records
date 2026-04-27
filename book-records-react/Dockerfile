# --- Stage 1: Build the React application ---
FROM node:lts-alpine AS build-site
WORKDIR /app
COPY ./package*.json ./
RUN npm ci
ARG VITE_API_BASE_URL
ARG VITE_API_KEY
ARG VITE_RESOURCE_BASE_URL
ARG VITE_OLLAMA_BASE_URL
ARG VITE_OLLAMA_MODEL
ARG VITE_OLLAMA_API_KEY
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
