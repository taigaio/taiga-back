# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC


from django.core.management import call_command

from taiga.celery import app


@app.task
def flush_expired_tokens():
    """Flushes any expired tokens in the outstanding token list."""
    call_command('flushexpiredtokens')
