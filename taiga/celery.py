# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import absolute_import, unicode_literals
import random
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.common")

from django.conf import settings

app = Celery('taiga')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if settings.ENABLE_TELEMETRY:
    rng = random.Random(settings.SECRET_KEY)
    hour = rng.randint(0, 4)
    minute = rng.randint(0, 59)
    app.conf.beat_schedule['send-telemetry-once-a-day'] = {
        'task': 'taiga.telemetry.tasks.send_telemetry',
        'schedule': crontab(minute=minute, hour=hour),
        'args': (),
    }

if settings.SEND_BULK_EMAILS_WITH_CELERY and settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL > 0:
    app.conf.beat_schedule['send-bulk-emails'] = {
        'task': 'taiga.projects.notifications.tasks.send_bulk_email',
        'schedule': settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL,
        'args': (),
    }

if ('taiga.auth.token_denylist' in settings.INSTALLED_APPS and
        getattr(settings, "FLUSH_REFRESHED_TOKENS_PERIODICITY", None)):
    app.conf.beat_schedule['auth-flush-expired-tokens'] = {
        'task': 'taiga.auth.token_denylist.tasks.flush_expired_tokens',
        'schedule': settings.FLUSH_REFRESHED_TOKENS_PERIODICITY,
        'args': (),
    }
