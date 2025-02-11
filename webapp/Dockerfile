### BASE ###
# Use the official Node image
FROM node:22-alpine as base

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./
RUN npm install --frozen-lockfile

# Copy all application files
COPY . .


### DEVELOPMENT ###
FROM base as dev

# Expose port for the development server
EXPOSE 2825

# Run the application in dev mode
CMD ["npm", "run", "dev"]


# Multi-stage docker build (to reduce the size of the final image)
### BUILD STAGE ###
# Use the official Node image
FROM base as build

# Build the application
RUN npm run build

### TEST STAGE ###
FROM base as test

# Copy the built application
COPY --from=build /app /app

# Run tests
CMD ["npm", "test"]


### PROD STAGE ###
FROM nginx:stable-alpine AS prod

# Copy only the files necessary to run the application, and leave behind the build environment
COPY --from=build /app/dist /usr/share/nginx/html

# Expose default NGINX port
EXPOSE 80

# Run Nginx
CMD ["nginx", "-g", "daemon off;"]

# Optional: Add health check
# HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost/ || exit 1

# Helper command to install node packages
FROM node:22-alpine as npm-install

WORKDIR /app

COPY package.json ./