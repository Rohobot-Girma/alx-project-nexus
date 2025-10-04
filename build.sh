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
    echo "=== Creating default superuser if not exists ==="
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@example.com', 'adminpassword') if not User.objects.filter(email='admin@example.com').exists() else None" | python manage.py shell
else
    echo "No DATABASE_URL set - using SQLite for local development"
    echo "=== Applying database migrations ==="
    python manage.py migrate
fi

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Build completed successfully ==="