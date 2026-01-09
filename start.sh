#!/bin/bash
set -e

echo "Starting deployment..."

# Run collectstatic (non-critical, continue on failure)
echo "Collecting static files..."
/opt/venv/bin/python manage.py collectstatic --noinput || echo "Warning: collectstatic failed, continuing..."

# Run migrations (non-critical for health check, continue on failure)
echo "Running migrations..."
/opt/venv/bin/python manage.py migrate --noinput || echo "Warning: migrations failed, continuing..."

# Start gunicorn (this must succeed)
echo "Starting gunicorn on port $PORT..."
exec /opt/venv/bin/gunicorn foodanalysis.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
