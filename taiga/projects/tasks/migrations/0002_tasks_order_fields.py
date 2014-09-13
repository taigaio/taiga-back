# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='taskboard_order',
            field=models.IntegerField(default=1, verbose_name='taskboard order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='task',
            name='us_order',
            field=models.IntegerField(default=1, verbose_name='us order'),
            preserve_default=True,
        ),
    ]
