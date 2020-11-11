#!/usr/bin/env bash
set -euo pipefail

# Give permission to taiga:taiga after mounting volumes
echo Give permission to taiga:taiga
chown -R taiga:taiga /taiga-back

# Start Celery processes
echo Starting Celery...
exec gosu taiga celery -A taiga.celery worker \
    --concurrency 4 \
    -l DEBUG \
    "$@"
