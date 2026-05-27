#!/bin/sh

echo "======================================"
echo "  PVD Goldsmith Manufacturing System  "
echo "======================================"

# Abort on any unhandled error
set -e

# Ensure the data directory exists (the named volume is mounted here)
mkdir -p /app/data /app/media /app/staticfiles

echo "[1/4] Running database migrations..."
python manage.py migrate --noinput

echo "[2/4] Loading initial data..."
python manage.py setup_initial_data

echo "[3/4] Collecting static files..."
python manage.py collectstatic --noinput

echo "[4/4] Starting Gunicorn server..."
echo ""
echo "  Open in browser: http://localhost:8000"
echo "  Login:           admin / admin123"
echo ""

exec gunicorn goldsmith.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
