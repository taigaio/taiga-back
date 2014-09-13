# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0003_auto_20140917_1405'),
    ]

    operations = [
        migrations.AddField(
            model_name='historyentry',
            name='is_hidden',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
