# DEMO DOCKERFILE: REPLACE WITH ACTUAL DB DOCKERFILE

### BASE ###
# Use the official Node image
FROM alpine:latest as base

# Copy all application files
COPY . .


### DEVELOPMENT ###
FROM base as dev

# Expose port for the development server
# TODO

# Start the database:
# TODO


# Multi-stage docker build (to reduce the size of the final image)
### BUILD STAGE ###
# Use the official Node image
FROM base as build

# Build the application
# TODO

### TEST STAGE ###
FROM base as test

# Run tests
# TODO


### PROD STAGE ###
FROM alpine AS prod

# Expose default NGINX port
EXPOSE 80


