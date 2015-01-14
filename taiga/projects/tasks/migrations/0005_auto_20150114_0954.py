# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_auto_20141210_1107'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['project', 'created_date', 'ref'], 'permissions': (('view_task', 'Can view task'),), 'verbose_name_plural': 'tasks', 'verbose_name': 'task'},
        ),
    ]
