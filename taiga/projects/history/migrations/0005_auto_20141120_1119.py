# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0004_historyentry_is_hidden'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historyentry',
            name='key',
            field=models.CharField(default=None, blank=True, max_length=255, db_index=True, null=True),
        ),
    ]
