#!/usr/bin/env bash
# build.sh - Build script for deployment
set -o errexit

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Applying database migrations ==="
python manage.py migrate

echo "=== Build completed successfully ==="