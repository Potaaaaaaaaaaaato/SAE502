# Monitoring Service Dockerfile
# Lightweight Python container for healthcheck and alerting

FROM python:3.11-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install required packages
RUN apk add --no-cache \
    postgresql-client \
    redis \
    curl

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests \
    psycopg2-binary \
    redis

# Copy healthcheck script
COPY healthcheck.py .
RUN chmod +x healthcheck.py

# Create non-root user
RUN adduser -D -u 1000 monitor
USER monitor

# Run healthcheck script periodically (every 5 minutes)
CMD ["sh", "-c", "while true; do python healthcheck.py; sleep 300; done"]
