# -*- coding: utf-8 -*-
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
