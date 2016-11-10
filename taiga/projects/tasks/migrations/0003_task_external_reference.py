# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_tasks_order_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='external_reference',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=False, null=False), blank=True, default=None, null=True, size=None, verbose_name='external reference'),
            preserve_default=True,
        ),
    ]
