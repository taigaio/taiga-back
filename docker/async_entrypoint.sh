#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

set -euo pipefail

# Give permission to taiga:taiga after mounting volumes
echo Give permission to taiga:taiga
chown -R taiga:taiga /taiga-back

# Start Celery processes
echo Starting Celery...
exec gosu taiga celery -A taiga.celery worker -B \
    --concurrency 4 \
    -l INFO \
    "$@"
