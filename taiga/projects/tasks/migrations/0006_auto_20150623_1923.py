# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_auto_20150114_0954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.ForeignKey(blank=True, null=True, to='projects.TaskStatus', related_name='tasks', verbose_name='status', on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
