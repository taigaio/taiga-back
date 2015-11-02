# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_watched'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historychangenotification',
            name='history_entries',
            field=models.ManyToManyField(verbose_name='history entries', to='history.HistoryEntry', related_name='+'),
        ),
        migrations.AlterField(
            model_name='historychangenotification',
            name='notify_users',
            field=models.ManyToManyField(verbose_name='notify users', to=settings.AUTH_USER_MODEL, related_name='+'),
        ),
    ]
