# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_auto_20141210_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstorystatus',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='is archived'),
            preserve_default=True,
        ),
    ]
