#!/usr/bin/env bash
set -euo pipefail

tail -n 0 -f /srv/logs/*.log &

# Start Taiga processes
echo Starting Taiga API...
exec gunicorn taiga.wsgi:application \
    --name taiga_api \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-tmp-dir /dev/shm \
    --log-level=info \
    --log-file=${LOG_FILE} \
    --access-logfile=${ACCESS_LOGFILE} \
    "$@"
