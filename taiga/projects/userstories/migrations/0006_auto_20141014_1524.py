# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0005_auto_20141009_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userstory',
            name='backlog_order',
            field=models.IntegerField(default=10000, verbose_name='backlog order'),
        ),
        migrations.AlterField(
            model_name='userstory',
            name='kanban_order',
            field=models.IntegerField(default=10000, verbose_name='sprint order'),
        ),
        migrations.AlterField(
            model_name='userstory',
            name='sprint_order',
            field=models.IntegerField(default=10000, verbose_name='sprint order'),
        ),
    ]
