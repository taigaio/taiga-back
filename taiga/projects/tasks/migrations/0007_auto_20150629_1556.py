# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_auto_20150623_1923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='milestone',
            field=models.ForeignKey(to='milestones.Milestone', related_name='tasks', default=None, verbose_name='milestone', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True),
            preserve_default=True,
        ),
    ]
