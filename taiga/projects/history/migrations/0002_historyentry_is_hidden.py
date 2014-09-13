# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historyentry',
            name='is_hidden',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
