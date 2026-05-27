#!/bin/sh
set -e

echo "======================================"
echo "  PVD Goldsmith Manufacturing System  "
echo "======================================"

# Ensure the data directory exists (mounted volume)
mkdir -p /app/data

echo "[1/4] Running database migrations..."
python manage.py migrate --noinput

echo "[2/4] Loading initial data..."
python manage.py setup_initial_data

echo "[3/4] Collecting static files..."
python manage.py collectstatic --noinput || true

echo "[4/4] Starting server..."
echo ""
echo "  Open in browser: http://localhost:8000"
echo "  Login:           admin / admin123"
echo ""

exec python manage.py runserver 0.0.0.0:8000
