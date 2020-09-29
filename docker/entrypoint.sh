#!/usr/bin/env bash
set -euo pipefail

# Execute pending migrations
echo Executing pending migrations
python manage.py migrate

# Load default templates
echo Load default templates
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
