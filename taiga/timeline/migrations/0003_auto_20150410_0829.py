# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0002_auto_20150327_1056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeline',
            name='event_type',
            field=models.CharField(db_index=True, max_length=250),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='timeline',
            name='namespace',
            field=models.CharField(default='default', max_length=250, db_index=True),
            preserve_default=True,
        ),
    ]
