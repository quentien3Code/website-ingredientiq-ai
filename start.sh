#!/bin/bash
set -e

echo "Starting deployment..."

COLLECTSTATIC_REQUIRED=${COLLECTSTATIC_REQUIRED:-false}
MIGRATIONS_REQUIRED=${MIGRATIONS_REQUIRED:-true}

# Run collectstatic (non-critical, continue on failure)
echo "Collecting static files..."
if ! /opt/venv/bin/python manage.py collectstatic --noinput; then
	if [ "${COLLECTSTATIC_REQUIRED}" = "true" ]; then
		echo "collectstatic failed and COLLECTSTATIC_REQUIRED=true; exiting."
		exit 1
	fi
	echo "Warning: collectstatic failed, continuing..."
fi

# Run migrations (non-critical for health check, continue on failure)
echo "Running migrations..."
if ! /opt/venv/bin/python manage.py migrate --noinput; then
	if [ "${MIGRATIONS_REQUIRED}" = "true" ]; then
		echo "migrations failed and MIGRATIONS_REQUIRED=true; exiting."
		exit 1
	fi
	echo "Warning: migrations failed, continuing..."
fi

# Start gunicorn (this must succeed)
echo "Starting gunicorn on port $PORT..."
exec /opt/venv/bin/gunicorn foodanalysis.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
