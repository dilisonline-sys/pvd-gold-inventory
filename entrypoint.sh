#!/bin/sh
set -e

echo "======================================"
echo "  PVD Goldsmith Manufacturing System  "
echo "======================================"

echo "[1/4] Running database migrations..."
python manage.py migrate --noinput

echo "[2/4] Setting up initial data..."
python manage.py setup_initial_data --skip-demo-user 2>/dev/null || true
# Create demo users only on first run (idempotent)
python manage.py setup_initial_data 2>/dev/null || true

echo "[3/4] Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

echo "[4/4] Starting server on port 8000..."
echo ""
echo "  App is ready at: http://localhost:8000"
echo "  Admin login:     admin / admin123"
echo ""
exec python manage.py runserver 0.0.0.0:8000
