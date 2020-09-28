#!/usr/bin/env bash
set -euo pipefail

# Execute pending migrations
echo Executing pending migrations
python manage.py migrate

# Load initial user and templates (if they don't exist)
echo "Load initial user and templates (if they dont exist)"
python manage.py loaddata initial_user
python manage.py loaddata initial_project_templates

# Start Taiga processes
echo Starting Taiga API...
exec gunicorn taiga.wsgi:application \
    --name taiga_api \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-tmp-dir /dev/shm \
    --log-level=info \
    --access-logfile - \
    "$@"
