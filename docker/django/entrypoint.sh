#!/bin/bash
set -e

echo "🚀 Starting Django application..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is up!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until python -c "import redis; client = redis.Redis(host='${REDIS_HOST:-redis}', port=${REDIS_PORT:-6379}); client.ping()" 2>/dev/null; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done
echo "✅ Redis is up!"

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
# Note: Commented out for local dev due to Docker volume permissions
# In production, Ansible will handle this differently
echo "📁 Skipping collectstatic for local dev..."
# python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional, for development)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "👤 Creating superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
fi

echo "✨ Django application is ready!"
echo "🎯 Starting Gunicorn..."

# Execute the main command (Gunicorn)
exec "$@"
