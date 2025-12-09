# Nginx Dockerfile
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/django.conf

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/mediafiles /app/docs/_build/html

# Create directory for Let's Encrypt challenges
RUN mkdir -p /var/www/certbot

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
