#!/usr/bin/env bash
# build.sh - Build script for deployment
set -o errexit

echo "=== Upgrading pip ==="
pip install --upgrade pip

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Checking for database configuration ==="
if [ -n "$DATABASE_URL" ]; then
    echo "PostgreSQL database detected - applying migrations"
    echo "=== Applying database migrations ==="
    python manage.py migrate
else
    echo "No DATABASE_URL set - using SQLite (development mode)"
    echo "=== Skipping migrations for SQLite (Python 3.13 compatibility) ==="
    # Skip migrations to avoid SQLite compatibility issues with Python 3.13
fi

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Build completed successfully ==="
