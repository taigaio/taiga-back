# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0002_webhook_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhooklog',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 22, 10, 21, 17, 188643), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='webhooklog',
            name='duration',
            field=models.FloatField(default=0, verbose_name='Duration'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='webhooklog',
            name='request_headers',
            field=django_pgjson.fields.JsonField(default={}, verbose_name='Request headers'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='webhooklog',
            name='response_headers',
            field=django_pgjson.fields.JsonField(default={}, verbose_name='Response headers'),
            preserve_default=True,
        ),
    ]
