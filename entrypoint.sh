#!/bin/sh

echo "======================================"
echo "  PVD Goldsmith Manufacturing System  "
echo "======================================"

# Ensure the data directory exists (the named volume is mounted here)
mkdir -p /app/data /app/media /app/staticfiles

echo "[1/4] Running database migrations..."
if ! python manage.py migrate --noinput; then
    echo "ERROR: Database migration failed. Aborting." >&2
    exit 1
fi

echo "[2/4] Loading initial data..."
if ! python manage.py setup_initial_data; then
    echo "WARNING: setup_initial_data failed — continuing anyway." >&2
fi

echo "[3/4] Collecting static files..."
python manage.py collectstatic --noinput || echo "WARNING: collectstatic failed — continuing anyway."

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
