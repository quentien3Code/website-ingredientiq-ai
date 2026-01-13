#!/bin/bash
set -e

echo "Starting deployment..."

COLLECTSTATIC_REQUIRED=${COLLECTSTATIC_REQUIRED:-false}
MIGRATIONS_REQUIRED=${MIGRATIONS_REQUIRED:-true}

# Prefer the Python provided by the runtime (Railpack puts it on PATH).
# Fall back to the legacy Nixpacks venv path if present.
if command -v python >/dev/null 2>&1; then
	PYTHON_CMD="python"
elif command -v python3 >/dev/null 2>&1; then
	PYTHON_CMD="python3"
elif [ -x /opt/venv/bin/python ]; then
	PYTHON_CMD="/opt/venv/bin/python"
else
	echo "Error: Python executable not found (python/python3 or /opt/venv/bin/python)."
	exit 1
fi

APP_PORT=${PORT:-8000}

# Run collectstatic (non-critical, continue on failure)
echo "Collecting static files..."
if ! "$PYTHON_CMD" manage.py collectstatic --noinput; then
	if [ "${COLLECTSTATIC_REQUIRED}" = "true" ]; then
		echo "collectstatic failed and COLLECTSTATIC_REQUIRED=true; exiting."
		exit 1
	fi
	echo "Warning: collectstatic failed, continuing..."
fi

# Run migrations (non-critical for health check, continue on failure)
echo "Running migrations..."
if ! "$PYTHON_CMD" manage.py migrate --noinput; then
	if [ "${MIGRATIONS_REQUIRED}" = "true" ]; then
		echo "migrations failed and MIGRATIONS_REQUIRED=true; exiting."
		exit 1
	fi
	echo "Warning: migrations failed, continuing..."
fi

# Create/reset superadmin if ADMIN_PASSWORD is set (one-time setup)
if [ -n "${ADMIN_PASSWORD}" ]; then
	ADMIN_EMAIL="${ADMIN_EMAIL:-admin@ingredientiq.ai}"
	echo "Creating/resetting superadmin: $ADMIN_EMAIL"
	"$PYTHON_CMD" manage.py reset_superadmin --email "$ADMIN_EMAIL" --password-env ADMIN_PASSWORD || echo "Warning: superadmin setup failed"
fi

# Start gunicorn (this must succeed)
echo "Starting gunicorn on port $APP_PORT..."
exec "$PYTHON_CMD" -m gunicorn foodanalysis.wsgi:application --bind "0.0.0.0:$APP_PORT" --workers 2 --timeout 120
